// app/page.tsx
"use client"

import React, { useState, useCallback, useMemo } from 'react';
// REMOVED: import { PredictionChart } from '@/components/PredictionChart';
import { Button } from "@/components/ui/button"; // Assuming shadcn/ui button
import { Input } from "@/components/ui/input";   // Assuming shadcn/ui input
import { Label } from "@/components/ui/label";   // Assuming shadcn/ui label
// Keep Card, CardContent, CardHeader, CardTitle, CardDescription for the table card
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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

// Removed COLORS and getColorForIndex as they were only for the chart


const PredictionPage = () => {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  // REMOVED: const [chartData, setChartData] = useState<{ name: string; value: number; fill: string }[]>([]);
  const [predictionResults, setPredictionResults] = useState<PredictionResult[]>([]); // Store raw results
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
      // REMOVED: setChartData([]); // Clear previous results
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
    // REMOVED: setChartData([]);
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

      // REMOVED: Chart data processing logic
      // --- Data Processing for Chart (Sum of ALL Confidences for EACH Class across all images) ---
      // const aggregatedConfidences: { [key: string]: number } = {};
      // const classNamesOrder = new Map<string, number>();
      // ... (rest of chart data processing)
      // setChartData(processedChartData);


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

  // totalImagesProcessed is still useful for context, though not explicitly shown on the chart anymore
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
            className="mt-4 bg-green-700"
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

      {/* REMOVED: Chart rendering section */}
      {/*
            {!loading && predictionResults.length > 0 && (
                 <div className="w-full max-w-md mx-auto">
                    <PredictionChart data={chartData} totalImageCount={totalImagesProcessed} />
                 </div>
            )}
            */}

      {/* REMOVED: Message if chart data is zero */}
      {/*
            {!loading && predictionResults.length > 0 && chartData.length === 0 && !error && (
                  <div className="flex justify-center items-center h-32">
                      <p className="text-muted-foreground">No valid predictions with confidence > 0 received to display on the chart.</p>
                  </div>
             )}
             */}


      {/* Display individual prediction results in a table */}
      {/* Show table if not loading AND there are prediction results */}
      {!loading && predictionResults.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Prediction Results</CardTitle> {/* Simplified title */}
            <CardDescription>Top predictions for each uploaded image.</CardDescription> {/* Simplified description */}
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Prediction</TableHead>
                  <TableHead className="text-right">Confidence</TableHead> {/* Keep right align for numbers */}
                </TableRow>
              </TableHeader>
              <TableBody>
                {predictionResults.map((result) => {
                  // Handle cases where top_predictions array is missing or empty
                  if (!result.top_predictions || result.top_predictions.length === 0) {
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
                        const confidencePercent = (prediction.confidence * 100).toFixed(2) + '%'; // Format as percentage

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
                              {isErrorEntry ? 'N/A' : confidencePercent} {/* Display formatted percentage */}
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

      {/* Message when no files selected yet or no results */}
      {!loading && predictionResults.length === 0 && !error && (
        <div className="flex justify-center items-center h-32">
          <p className="text-muted-foreground">Select images and click &quot;Predict Diseases&quot; to see results.</p>
        </div>
      )}
    </div>
  );
}

export default PredictionPage;