import React, { useState, useRef } from "react";
import { AlertCircle, FileText, Upload } from "lucide-react";

const Alert = ({ children, variant = "info", className = "" }) => {
  const colors = {
    info: "bg-blue-50 text-blue-800 border-blue-200",
    error: "bg-red-50 text-red-800 border-red-200",
  };

  return (
    <div className={`flex items-center gap-2 p-4 border rounded-lg ${colors[variant]} ${className}`}>
      {children}
    </div>
  );
};

const DocumentProcessor = () => {
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const processFile = async (file) => {
    if (!file) return;

    const validTypes = ["application/pdf", "image/png", "image/jpeg", "image/tiff"];
    if (!validTypes.includes(file.type)) {
      setError("Invalid file type. Please upload a PDF or image file (PNG, JPG, TIFF).");
      return;
    }

    setProcessing(true);
    setError(null);
    setResults(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/analyze-content", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleDragEnter = (e) => e.preventDefault() || setIsDragActive(true);
  const handleDragLeave = (e) => e.preventDefault() || setIsDragActive(false);
  const handleDragOver = (e) => e.preventDefault();
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    processFile(e.dataTransfer.files[0]);
  };

  const handleFileInput = (e) => processFile(e.target.files[0]);
  const handleClick = () => fileInputRef.current?.click();

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Social Media Content Analyzer</h1>

      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.tiff"
          onChange={handleFileInput}
        />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg text-gray-600">
          {isDragActive ? "Drop the file here..." : "Drag 'n' drop a file here, or click to select"}
        </p>
        <p className="text-sm text-gray-500 mt-2">Supports PDF and image files (PNG, JPG, TIFF)</p>
      </div>

      {processing && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <span>Processing your document... Please wait</span>
        </Alert>
      )}

      {error && (
        <Alert variant="error">
          <AlertCircle className="h-4 w-4" />
          <span>Error processing document: {error}</span>
        </Alert>
      )}

      {results && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
          <div className="mb-6 p-4 bg-white rounded-lg shadow">
            <h3 className="font-medium mb-2">Sentiment Analysis</h3>
            {results.results.map((result, index) => (
              <div key={index} className="mb-4">
                <p><strong>Text:</strong> {result.text}</p>
                <p><strong>Sentiment:</strong> {result.sentiment}</p>
                <p><strong>Confidence:</strong> {Math.round(result.confidence * 100)}%</p>
              </div>
            ))}

            <h3 className="font-medium mb-2">Engagement Suggestions</h3>
            <ul className="list-disc ml-5">
              {results.suggestions.map((suggestion, index) => (
                <li key={index}>{suggestion}</li>
              ))}
            </ul>
          </div>

          <h3 className="font-medium mb-2">Extracted Pages</h3>
          {results.pages.map((page, index) => (
            <div key={index} className="mb-6 p-4 bg-white rounded-lg shadow">
              <div className="flex items-center mb-2">
                <FileText className="h-5 w-5 mr-2 text-gray-500" />
                <h3 className="font-medium">Page {page.page_number}</h3>
                <span className="ml-auto text-sm text-gray-500">Confidence: {Math.round(page.confidence * 100)}%</span>
              </div>
              <p className="whitespace-pre-wrap text-gray-700">{page.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentProcessor;
