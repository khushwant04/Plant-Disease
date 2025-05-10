// app/page.tsx
"use client"

import React, { useState, useCallback, useMemo } from 'react';
import { PredictionChart } from '@/components/PredictionChart'; // Adjust path if necessary
import { Button } from "@/components/ui/button"; // Assuming shadcn/ui button
import { Input } from "@/components/ui/input";   // Assuming shadcn/ui input
import { Label } from "@/components/ui/label";   // Assuming shadcn/ui label
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"; // Assuming shadcn/ui card
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"; // Assuming shadcn/ui alert
import { Terminal, Loader2 } from "lucide-react"; // Icons
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table" // Assuming shadcn/ui table for individual results


// Define interfaces for the API response structure (same as before)
interface TopPrediction {
  class_index: number | null;
  class_name: string;
  confidence: number;
}

interface PredictionResult {
  filename: string;
  top_predictions: TopPrediction[]; // This array can contain multiple predictions per image
}

interface ApiResponse {
  predictions: PredictionResult[];
}

// Simple color palette function (same as before)
const COLORS = [
  '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28DFF',
  '#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9', '#92A8CD',
  '#F45B69', '#80A4ED', '#D0EEB9', '#FFDAB9', '#E9E9EB'
];

const getColorForIndex = (index: number) => COLORS[index % COLORS.length];


const PredictionPage = () => {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  // chartData stores aggregated summed confidences for each class
  const [chartData, setChartData] = useState<{ name: string; value: number; fill: string }[]>([]);
  const [predictionResults, setPredictionResults] = useState<PredictionResult[]>([]); // Store raw results
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
      setChartData([]); // Clear previous results
      setPredictionResults([]);
      setError(null);
    }
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setError("Please select files to upload.");
      return;
    }

    setLoading(true);
    setError(null);
    setChartData([]);
    setPredictionResults([]);

    const formData = new FormData();
    for (let i = 0; i < selectedFiles.length; i++) {
      formData.append('files', selectedFiles[i]); // 'files' must match the FastAPI endpoint parameter name
    }

    const fastapiEndpoint = 'http://localhost:8000/predict/'; // Adjust if necessary

    try {
      const response = await fetch(fastapiEndpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.detail
          ? (typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail))
          : JSON.stringify(errorData);
        throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorMessage}`);
      }

      const result: ApiResponse = await response.json();
      setPredictionResults(result.predictions); // Store raw results

      // --- Data Processing for Chart (Sum of ALL Confidences for EACH Class across all images) ---
      const aggregatedConfidences: { [key: string]: number } = {};
      // Use a Map to maintain insertion order for consistent color assignment
      const classNamesOrder = new Map<string, number>(); // Map<className, index>


      result.predictions.forEach(prediction => {
        // Process results that have predictions
        if (prediction.top_predictions && prediction.top_predictions.length > 0) {
          // Iterate through *all* top predictions for this image
          prediction.top_predictions.forEach(topPred => {
            const className = topPred.class_name;
            const confidence = topPred.confidence;

            // Skip error entries for confidence aggregation
            if (className && className.startsWith("Error processing file")) {
              return;
            }

            // Aggregate confidence for this class
            if (!aggregatedConfidences[className]) {
              aggregatedConfidences[className] = 0;
              if (!classNamesOrder.has(className)) {
                classNamesOrder.set(className, classNamesOrder.size); // Add new class to order map
              }
            }
            aggregatedConfidences[className] += confidence; // Sum the confidence


          }); // End inner loop over top_predictions
        }
      }); // End outer loop over predictions

      // Convert aggregatedConfidences into the chart data format
      const processedChartData: { name: string; value: number; fill: string }[] = [];

      // Iterate through the classes in the order they were first encountered
      Array.from(classNamesOrder.keys()).forEach((className) => {
        // Only add classes that actually received some confidence value > 0
        if (aggregatedConfidences[className] > 0) {
          processedChartData.push({
            name: className,
            value: aggregatedConfidences[className],
            fill: getColorForIndex(classNamesOrder.get(className)!) // Assign color based on its index in the discovery order
          });
        }
      });

      // Optional: Sort the chart data (e.g., by value descending) for consistent appearance
      processedChartData.sort((a, b) => b.value - a.value); // Sort by summed confidence descending


      setChartData(processedChartData);

    } catch (err) {
      console.error("Upload failed:", err);
      if (err instanceof Error) {
        setError(`Upload failed: ${err.message}`);
      } else {
        setError("An unknown error occurred during upload.");
      }

    } finally {
      setLoading(false);
    }
  }, [selectedFiles]);

  // Total images processed count for the table and chart context
  const totalImagesProcessed = useMemo(() => {
    return predictionResults.length;
  }, [predictionResults]);


  return (
    <div className="container mx-auto p-4">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Upload Images for Plant Disease Prediction</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid w-full max-w-sm items-center gap-1.5">
            <Label htmlFor="picture">Select Images</Label>
            <Input
              id="picture"
              type="file"
              multiple // Allows selecting multiple files
              accept="image/*" // Only allow image files
              onChange={handleFileChange}
              className="cursor-pointer"
            />
            <p className="text-sm text-muted-foreground">Select one or more plant images (e.g., leaves).</p>
          </div>
          <Button
            onClick={handleSubmit}
            disabled={!selectedFiles || selectedFiles.length === 0 || loading}
            className="mt-4"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Predicting...
              </>
            ) : (
              "Predict Diseases"
            )}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <Terminal className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Show loading spinner if loading */}
      {loading && (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {/* Render the chart if data is available and not loading */}
      {/* Also ensure there are results to display before showing the chart card */}
      

      {/* Show a message if no valid predictions for chart after loading */}
      {!loading && predictionResults.length > 0 && chartData.length === 0 && !error && (
        <div className="flex justify-center items-center h-32">
          <p className="text-muted-foreground">No valid predictions with confidence > 0 received to display on the chart.</p>
        </div>
      )}


      {/* Display individual prediction results in a table */}
      {!loading && predictionResults.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Individual Image Results (Top 10 Predictions)</CardTitle>
            {/* Using CardDescription - requires import */}
            <CardDescription>Top 10 predictions for each uploaded image.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Prediction</TableHead> {/* Changed to "Prediction" */}
                  <TableHead className="text-right">Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {predictionResults.map((result) => {
                  // Display all top_predictions for each file in the table
                  if (!result.top_predictions || result.top_predictions.length === 0) {
                    // Handle cases where top_predictions array is missing or empty
                    const isError = result.top_predictions && result.top_predictions.length > 0 && result.top_predictions[0].class_name.startsWith("Error processing file");
                    return (
                      <TableRow key={result.filename} className={isError ? "bg-red-50/50" : ""}>
                        <TableCell className="font-medium">{result.filename}</TableCell>
                        <TableCell colSpan={2} className={isError ? "text-red-700" : ""}>
                          {isError ? `Error: ${result.top_predictions[0].class_name.replace("Error processing file: ", "")}` : "No predictions returned"}
                        </TableCell>
                      </TableRow>
                    );
                  }

                  return (
                    <>
                      {result.top_predictions.map((prediction, predIndex) => {
                        const isErrorEntry = prediction.class_name && prediction.class_name.startsWith("Error processing file");
                        return (
                          <TableRow key={`${result.filename}-${predIndex}`} className={isErrorEntry ? "bg-red-50/50" : ""}>
                            {/* Only show filename on the first row for each image */}
                            {predIndex === 0 ? (
                              <TableCell rowSpan={result.top_predictions.length} className="font-medium align-top border-b">
                                {result.filename}
                              </TableCell>
                            ) : null}
                            <TableCell className={isErrorEntry ? "text-red-700" : ""}>
                              {isErrorEntry ? `Error: ${prediction.class_name.replace("Error processing file: ", "")}` : prediction.class_name}
                            </TableCell>
                            <TableCell className="text-right">
                              {isErrorEntry ? 'N/A' : prediction.confidence.toFixed(4)}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Message when no files selected yet */}
      {!loading && predictionResults.length === 0 && (!selectedFiles || selectedFiles.length === 0) && !error && (
        <div className="flex justify-center items-center h-32">
          <p className="text-muted-foreground">Select images and click "Predict Diseases" to see results.</p>
        </div>
      )}
    </div>
  );
}

export default PredictionPage;