const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path'); // Import the path module

const app = express();
const port = 8080;

// Middleware to parse JSON requests
app.use(bodyParser.json());

// Serve the HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.get('/api/data', (req, res) => {
	// Read data from the JSON file
	fs.readFile('data.json', 'utf8', (err, data) => {
		if (err) {
			console.error(err);
			res.status(500).json({ error: 'Internal Server Error' });
		} else {
			res.json(JSON.parse(data));
		}
	});
});

app.post('/api/data', (req, res) => {
	// Assuming req.body contains the new data
	const { instruction } = req.body;
  
	if (instruction == "auto" 
	|| instruction == "forward" 
	|| instruction == "backward"
	|| instruction == "left" 
	|| instruction == "right" 
	|| instruction == "straight" 
	|| instruction == "stop") {
		// Write the new data directly to the JSON file, replacing existing content
		fs.writeFile('data.json', JSON.stringify(req.body), 'utf8', (writeErr) => {
			if (writeErr) {
			console.error(writeErr);
			res.status(500).json({ error: 'Internal Server Error' });
			} else {
			res.status(201).json(req.body);
			}
		});
	} else {
		res.status(418).send({message: "Invalid or Missing instruction parameter"})
	}
});

// Start the server
app.listen(port, () => {
	console.log(`Server is running at http://localhost:${port}`);
});
