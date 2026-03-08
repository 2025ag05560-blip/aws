/**
 * CSVUploader.jsx - React component for uploading CSV files to AWS Lambda
 * 
 * This component provides a file input and upload functionality for CSV files.
 * It sends the file to the Lambda function via API Gateway.
 */

import React, { useState } from 'react';

const CSVUploader = ({ apiEndpoint }) => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  /**
   * Handle file selection from input
   */
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
        setError('Please select a CSV file');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError('');
      setMessage('');
    }
  };

  /**
   * Convert file to base64 string
   */
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Extract base64 content (remove data:text/csv;base64, prefix)
        const base64String = reader.result.split(',')[1];
        resolve(base64String);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  /**
   * Handle file upload
   */
  const handleUpload = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    try {
      // Convert file to base64
      const base64Content = await fileToBase64(file);

      // Prepare request payload
      const payload = {
        filename: file.name,
        fileContent: base64Content,
      };

      // Make POST request to Lambda function
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.message || data.error || 'Upload failed');
        return;
      }

      setMessage(
        `✓ File uploaded successfully!\nS3 Path: ${data.s3_key}`
      );
      setFile(null);

      // Reset file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) {
        fileInput.value = '';
      }
    } catch (err) {
      setError(`Upload failed: ${err.message}`);
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>CSV File Uploader</h2>

        <form onSubmit={handleUpload} style={styles.form}>
          <div style={styles.inputGroup}>
            <label htmlFor="csv-input" style={styles.label}>
              Select CSV File:
            </label>
            <input
              id="csv-input"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              style={styles.fileInput}
              disabled={loading}
            />
          </div>

          {file && (
            <div style={styles.fileInfo}>
              📄 <strong>{file.name}</strong> ({(file.size / 1024).toFixed(2)} KB)
            </div>
          )}

          <button
            type="submit"
            disabled={!file || loading}
            style={{
              ...styles.button,
              opacity: !file || loading ? 0.6 : 1,
              cursor: !file || loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Uploading...' : 'Upload to S3'}
          </button>
        </form>

        {error && (
          <div style={styles.message} style={{ ...styles.message, ...styles.error }}>
            ⚠️ {error}
          </div>
        )}

        {message && (
          <div style={styles.message} style={{ ...styles.message, ...styles.success }}>
            {message}
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '20px',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
    padding: '40px',
    maxWidth: '500px',
    width: '100%',
  },
  title: {
    marginBottom: '30px',
    color: '#333',
    fontSize: '24px',
    fontWeight: '600',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  label: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  fileInput: {
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    cursor: 'pointer',
  },
  fileInfo: {
    padding: '12px',
    backgroundColor: '#e8f4f8',
    borderLeft: '3px solid #0077cc',
    borderRadius: '4px',
    fontSize: '14px',
    color: '#333',
  },
  button: {
    padding: '12px 24px',
    backgroundColor: '#0077cc',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: '600',
    transition: 'background-color 0.3s',
    marginTop: '10px',
  },
  message: {
    padding: '12px 16px',
    borderRadius: '4px',
    fontSize: '14px',
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word',
  },
  error: {
    backgroundColor: '#fee',
    color: '#c33',
    border: '1px solid #fcc',
  },
  success: {
    backgroundColor: '#d4edda',
    color: '#155724',
    border: '1px solid #c3e6cb',
  },
};

export default CSVUploader;
