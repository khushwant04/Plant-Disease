// components/PredictionChart.tsx
"use client"

import * as React from "react"
import { Label, Pie, PieChart, Cell } from "recharts"

import {
    Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle,
} from "@/components/ui/card"
import {
    ChartContainer, ChartTooltip, ChartTooltipContent,
} from "@/components/ui/chart"

interface ChartDataType {
    name: string;
    value: number; // This represents the summed confidence for this class
    fill: string;
}

interface PredictionChartProps {
    data: ChartDataType[];
    totalImageCount: number; // Total number of images processed (for context)
}

const COLORS = [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28DFF',
    '#FF6F61', '#6B5B95', '#88B04B', '#F7CAC9', '#92A8CD',
    '#F45B69', '#80A4ED', '#D0EEB9', '#FFDAB9', '#E9E9EB'
];

// No longer needed if using index from data map
// const getColorForIndex = (index: number) => COLORS[index % COLORS.length];

// Custom function to render labels on pie slices
const renderCustomizedLabel = ({ cx, cy, midAngle, outerRadius, value, name, percent }: any) => {
    const RADIAN = Math.PI / 180;
    // Position the label slightly outside the slice
    const radius = outerRadius * 1.2; // Adjust multiplier to move label further out
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    // Determine text anchor for better alignment
    const textAnchor = (x > cx ? 'start' : 'end');

    // Format the summed confidence value
    const formattedValue = value.toFixed(2); // Show 2 decimal places

    // Construct the label text
    // If the class name is very long, you might need to truncate it or wrap text.
    // For simplicity, we'll show name and value.
    const labelText = `${name}: ${formattedValue}`;

    return (
        <text
            x={x}
            y={y}
            fill="hsl(var(--foreground))" // Use foreground color from shadcn/ui
            textAnchor={textAnchor}
            dominantBaseline="central"
            fontSize={10} // Adjust font size if needed
        // Optional: Add a slight text shadow for readability against background
        // style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.3)' }}
        >
            {labelText}
        </text>
    );
};


export function PredictionChart({ data, totalImageCount }: PredictionChartProps) {
    if (!data || data.length === 0) {
        return (
            <Card className="flex flex-col">
                <CardHeader className="items-center pb-0">
                    <CardTitle>Prediction Results Chart</CardTitle>
                    <CardDescription>Distribution of summed confidence across all predicted classes.</CardDescription>
                </CardHeader>
                <CardContent className="flex-1 pb-0 flex items-center justify-center h-[250px]">
                    <p className="text-muted-foreground">No chart data available. Upload images or check individual results.</p>
                </CardContent>
            </Card>
        );
    }

    // Recalculate total value for the center label (sum of all values in the chart data)
    const totalSummedConfidenceInChart = React.useMemo(() => {
        return data.reduce((acc, curr) => acc + curr.value, 0);
    }, [data]);


    return (
        <Card className="flex flex-col">
            <CardHeader className="items-center pb-0">
                <CardTitle>Prediction Results Chart</CardTitle>
                <CardDescription>Distribution of summed confidence across all predicted classes from top results.</CardDescription> {/* Updated description */}
            </CardHeader>
            <CardContent className="flex-1 pb-0">
                <ChartContainer
                    config={{}}
                    className="mx-auto aspect-square max-h-[300px]" // Increased max height to accommodate labels outside
                >
                    <PieChart width={400} height={300}> {/* Adjusted chart dimensions if needed */}
                        <ChartTooltip
                            cursor={false}
                            // Tooltip still shows name and summed confidence on hover
                            content={<ChartTooltipContent nameKey="name" formatter={(value: number) => `${value.toFixed(2)} (Summed Confidence)`} />}
                        />
                        <Pie
                            data={data}
                            dataKey="value" // Use 'value' for slice size (summed confidence)
                            nameKey="name" // Use 'name' for class name
                            innerRadius={60}
                            outerRadius={80} // Define outer radius explicitly if using labels outside
                            stroke="#ffffff" // Add stroke for slice separation if desired
                            strokeWidth={2}
                            label={renderCustomizedLabel} // Add the custom label renderer
                            labelLine={false} // Hide connecting lines to labels if placing outside
                        >
                            {data.map((entry) => (
                                // Use unique class name as key for stability. Color is part of the entry data.
                                <Cell key={`cell-${entry.name}`} fill={entry.fill} />
                            ))}
                            <Label
                                content={({ viewBox }) => {
                                    if (viewBox && "cx" in viewBox && "cy" in viewBox) {
                                        return (
                                            <text
                                                x={viewBox.cx}
                                                y={viewBox.cy}
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                            >
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={viewBox.cy - 10} // Adjust position
                                                    className="fill-foreground text-xl font-bold" // Adjust font size
                                                >
                                                    {totalSummedConfidenceInChart.toFixed(2)} {/* Show total summed confidence in chart */}
                                                </tspan>
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={(viewBox.cy || 0) + 10} // Adjust position
                                                    className="fill-muted-foreground text-xs" // Smaller font
                                                >
                                                    Total Summed Conf.
                                                </tspan>
                                                {/* Add line for image count */}
                                                {totalImageCount > 0 && (
                                                    <tspan
                                                        x={viewBox.cx}
                                                        y={(viewBox.cy || 0) + 30}
                                                        className="fill-muted-foreground text-xs"
                                                    >
                                                        from {totalImageCount} Images
                                                    </tspan>
                                                )}
                                            </text>
                                        )
                                    }
                                    return null;
                                }}
                                position="center" // Ensure the center label is positioned correctly
                            />
                        </Pie>
                    </PieChart>
                </ChartContainer>
            </CardContent>
            <CardFooter className="flex-col gap-2 text-sm">
                <div className="leading-none text-muted-foreground">
                    Chart slices show the sum of confidence scores for each unique class appearing in the top predictions for all images. Labels display the class name and summed confidence.
                </div>
            </CardFooter>
        </Card>
    )
}