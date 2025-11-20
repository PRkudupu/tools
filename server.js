// server.js
const express = require('express');
const axios = require('axios');
const cors = require('cors');
const app = express();
const port = 3000;

// Replace this with your real Databricks PAT
const DATABRICKS_PAT = 'dapic6854bd4f0c39e91b51b99a2edfd86f1...';

// Allow cross-origin requests from browser
app.use(cors());
app.use(express.json());

// Proxy endpoint
app.post('/chat', async (req, res) => {
  try {
    const response = await axios.post(
      'https://adb-1355704782079007.7.azuredatabricks.net/serving-endpoints/cbt_1/invocations',
      req.body,
      {
        headers: {
          'Authorization': `Bearer ${DATABRICKS_PAT}`,
          'Content-Type': 'application/json'
        }
      }
    );
    res.json(response.data);
  } catch (error) {
    console.error('Proxy error:', error.message);
    res.status(error.response?.status || 500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Databricks proxy server listening at http://localhost:${port}`);
});
