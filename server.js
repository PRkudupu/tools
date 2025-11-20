// server.js
const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
const port = 3000;

// 🔐 TODO: paste your FULL Databricks PAT here (no "..." at the end)
const DATABRICKS_PAT = 'PASTE_FULL_TOKEN_HERE';

// 🔗 TODO: make sure this EXACTLY matches the URL that works in Postman
// e.g. "customer_pre_brief" or "cbt_1" depending on what you use there.
const DATABRICKS_ENDPOINT =
  'https://adb-1355704782079007.7.azuredatabricks.net/serving-endpoints/customer_pre_brief/invocations';
// If you actually use cbt_1 in Postman, then use this instead:
// const DATABRICKS_ENDPOINT =
//   'https://adb-1355704782079007.7.azuredatabricks.net/serving-endpoints/cbt_1/invocations';

app.use(cors());
app.use(express.json());

// Simple health check so we can test the server without Databricks
app.get('/health', (req, res) => {
  res.send('OK');
});

// Proxy endpoint that the HTML calls
app.post('/chat', async (req, res) => {
  try {
    console.log('➡️  Incoming /chat payload:', JSON.stringify(req.body));

    const response = await axios.post(DATABRICKS_ENDPOINT, req.body, {
      headers: {
        Authorization: `Bearer ${DATABRICKS_PAT}`,
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
    });

    console.log('✅ Databricks response status:', response.status);
    res.status(response.status).json(response.data);
  } catch (error) {
    if (error.response) {
      console.error('❌ Databricks error status:', error.response.status);
      console.error('❌ Databricks error data:', error.response.data);
      res.status(error.response.status).json(error.response.data);
    } else {
      console.error('❌ Proxy error:', error.message);
      res.status(500).json({ error: error.message });
    }
  }
});

app.listen(port, () => {
  console.log(`🚀 Databricks proxy server listening at http://localhost:${port}`);
});



npm init -y
npm install express axios cors
