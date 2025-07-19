const express = require('express');
const mongoose = require('mongoose');
require('dotenv').config();
const cors = require('cors');

const app = express();
const port = process.env.PORT || 3002;

// MongoDB connection URI: fallback to container hostname
const mongoURI = process.env.MONGO_URL || 'mongodb://mongo-db:27017/ankitdb';

mongoose.connect(mongoURI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log(" MongoDB connected successfully"))
.catch((err) => {
  console.error("❌ MongoDB connection error:", err);
  process.exit(1); // Exit if MongoDB is not reachable
});

app.use(express.json());
app.use(cors());

app.get('/health', (req, res) => {
  res.send({ status: 'OK' });
});

const userSchema = mongoose.Schema({
  name: {
    type: String,
    required: true,
    minlength: 1,
    maxlength: 200,
  },
  age: {
    type: Number,
    required: true,
  },
  createdAt: {
    type: Date,
    default: Date.now,
  },
});

const User = mongoose.model('user', userSchema);

app.post('/addUser', async (req, res) => {
  try {
    const { name, age } = req.body;
    if (!name || !age) {
      return res.status(400).json({ error: "Both name and age are required." });
    }

    const existingUser = await User.findOne({ name: name }); // FIXED: use findOne instead of find
    if (existingUser) {
      return res.status(409).json({ error: "User already exists." });
    }

    const newUser = new User({ name, age });
    await newUser.save();

    res.status(201).json({ msg: "User Added Successfully" });
  } catch (err) {
    console.error(err);
    res.status(500).json({ err: "Internal Server Error" });
  }
});

app.get('/fetchUser', async (req, res) => {
  try {
    const users = await User.find({});
    if (users.length > 0) {
      res.send(users);
    } else {
      res.send({ msg: "No users found" });
    }
  } catch (err) {
    console.error(err);
    res.status(500).send({ msg: "Something went wrong" });
  }
});

app.listen(port, () => {
  console.log(`🚀 Server is running on port ${port}`);
});
