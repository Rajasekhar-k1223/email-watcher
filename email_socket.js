const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const { createClient } = require("redis");

// Server setup
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: ['http://127.0.0.1:3000','http://157.173.199.49:3000',"https://mail.imailler.com","*"], // Adjust for your frontend
    methods: ["GET", "POST"],
  },
});

// Configure Redis client with authentication
const redisClient = createClient({
  socket: {
    host: "157.173.199.49",
    port: 6379,
  },
  password: "$2a$12$sDztpY8S1HX0NhnNNDcctezevP95TjwYJMkjHsA9anKzL7u92vUV2", // Redis password
});

redisClient.on("error", (err) => console.error("Redis Client Error", err));
redisClient.connect().then(() => console.log("Connected to Redis"));

// Listen for Socket.IO events
io.on("connection", (socket) => {
  console.log(`Client connected: ${socket.id}`);

  // Store socket ID in Redis
 socket.on("register_client", async (userId) => {
  try {
    // Store socket ID as a string
    await redisClient.set(userId, socket.id);
    console.log(`Registered user ${userId} with socket ID ${socket.id}`);
  } catch (err) {
    console.error(`Error registering user ${userId}:`, err);
  }
});

  // Listen for events from Python
 socket.on("email_inserted", async (data) => {
  console.log("New email inserted:", data);

  try {
    // const keys = await redisClient.keys("*"); // Get all user IDs
    // for (const userId of keys) {
      // Ensure the key holds a string value
      // const type = await redisClient.type(userId);
      // if (type !== "string") {
      //   console.warn(`Skipping key ${userId}: expected string but found ${type}`);
      //   continue;
      // }
    console.log(data.socket_id)
    console.log(data.user_email)
    const socketId = await redisClient.get(data.user_email);

    if (socketId) {
        console.log({"socket_id":socketId})
        io.to(socketId).emit("new_email", data);
        console.log(`Email event sent to user ${data.user_email} with socket ID ${socketId}`);
      }
    // }
  } catch (err) {
    console.error("Error handling email_inserted:", err);
  }
});

  // Handle disconnection
  socket.on("disconnect", async () => {
  console.log(`Client disconnected: ${socket.id}`);
  try {
    const keys = await redisClient.keys("*");
    for (const userId of keys) {
      const type = await redisClient.type(userId);
      if (type === "string") {
        const storedSocketId = await redisClient.get(userId);
        if (storedSocketId === socket.id) {
          await redisClient.del(userId);
          console.log(`Removed user ${userId} from Redis`);
          break;
        }
      }
    }
  } catch (err) {
    console.error("Error during disconnect handling:", err);
  }
});
});

// Start the server
const PORT = 8765;
const IP_ADDRESS = "0.0.0.0";
server.listen(PORT, IP_ADDRESS, () => {
  console.log(`Socket.IO server running on http://${IP_ADDRESS}:${PORT}`);
});
