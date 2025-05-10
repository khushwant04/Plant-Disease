from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import numpy as np
from google import genai
from google.genai import types
from app.config import PROJECT_ID, LOCATION, GEMINI_MODEL
from app.logging_config import logger

router = APIRouter()

@router.post("/generate-visualization/")
async def generate_visualization(
    request: dict = Body(..., example={"disease": "Apple Cedar Rust", "visualization_type": "treatment_effectiveness"})
):
    """Generate agricultural data visualizations based on disease information"""
    try:
        disease_name = request.get("disease", "")
        viz_type = request.get("visualization_type", "treatment_effectiveness")
        
        # Use Gemini to generate grounded data about the disease
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
        
        # Create prompt based on visualization type
        if viz_type == "treatment_effectiveness":
            prompt = f"""
            Generate realistic, evidence-based data about the effectiveness of different treatments for {disease_name} in plants.
            Return the data as a JSON object with this structure:
            {{
                "treatments": ["Treatment A", "Treatment B", "Treatment C", ...],
                "effectiveness_percentages": [85, 72, 65, ...],
                "cost_per_acre": [120, 80, 50, ...],
                "application_difficulty": [3, 2, 4, ...] (scale 1-5)
            }}
            Base your response on scientific literature and agricultural best practices.
            Only return the JSON object, nothing else.
            """
        elif viz_type == "disease_prevalence":
            prompt = f"""
            Generate realistic, evidence-based data about the prevalence of {disease_name} across different growing regions.
            Return the data as a JSON object with this structure:
            {{
                "regions": ["Northeast", "Midwest", "South", "West", "Northwest"],
                "prevalence_percentages": [12, 32, 8, 15, 22],
                "yearly_trend": [
                    {{ "year": 2020, "percentages": [10, 28, 7, 14, 20] }},
                    {{ "year": 2021, "percentages": [11, 29, 8, 15, 21] }},
                    {{ "year": 2022, "percentages": [12, 32, 8, 15, 22] }},
                    {{ "year": 2023, "percentages": [13, 34, 9, 16, 23] }},
                    {{ "year": 2024, "percentages": [15, 36, 10, 17, 24] }}
                ]
            }}
            Base your response on scientific literature and agricultural best practices.
            Only return the JSON object, nothing else.
            """
        else:
            prompt = f"""
            Generate realistic, evidence-based data about yield impact of {disease_name} on crop production.
            Return the data as a JSON object with this structure:
            {{
                "infection_severity": ["None", "Low", "Medium", "High", "Severe"],
                "yield_percentage": [100, 85, 65, 45, 20],
                "quality_impact": [0, 1, 2, 3, 4] (scale 0-4)
            }}
            Base your response on scientific literature and agricultural best practices.
            Only return the JSON object, nothing else.
            """
        
        contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
        config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.9,
            max_output_tokens=8000,
            response_modalities=["TEXT"]
        )
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config
        )
        
        # Parse JSON from response
        try:
            # Extract JSON from the response text
            json_text = response.text
            # Clean up potential markdown code blocks
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[0].strip()
            
            data = json.loads(json_text)
        except Exception as e:
            logger.error(f"Error while parsing JSON: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}, Response: {response.text[:200]}")
            return JSONResponse(status_code=400, content={"error": "Failed to parse data from AI response"})
        
        # Generate visualization based on data type
        plots = []
        if viz_type == "treatment_effectiveness":
            # Bar chart for effectiveness
            fig1 = {
                "data": [
                    {
                        "x": data["treatments"],
                        "y": data["effectiveness_percentages"],
                        "type": "bar",
                        "marker": {"color": "rgba(50, 171, 96, 0.7)"}
                    }
                ],
                "layout": {
                    "title": f"Treatment Effectiveness for {disease_name}",
                    "xaxis": {"title": "Treatment Method"},
                    "yaxis": {"title": "Effectiveness (%)"}
                }
            }
            
            # Scatter plot for cost vs effectiveness
            fig2 = {
                "data": [
                    {
                        "x": data["cost_per_acre"],
                        "y": data["effectiveness_percentages"],
                        "mode": "markers",
                        "type": "scatter",
                        "text": data["treatments"],
                        "marker": {
                            "size": 12,
                            "color": data["application_difficulty"],
                            "colorscale": "Viridis",
                            "showscale": True,
                            "colorbar": {"title": "Application Difficulty (1-5)"}
                        }
                    }
                ],
                "layout": {
                    "title": "Cost vs. Effectiveness",
                    "xaxis": {"title": "Cost per Acre ($)"},
                    "yaxis": {"title": "Effectiveness (%)"},
                    "hovermode": "closest"
                }
            }
            plots = [fig1, fig2]
            
        elif viz_type == "disease_prevalence":
            # Regional prevalence
            fig1 = {
                "data": [
                    {
                        "type": "choropleth",
                        "locationmode": "USA-states",
                        "locations": data["regions"],
                        "z": data["prevalence_percentages"],
                        "text": data["regions"],
                        "colorscale": "Reds",
                        "colorbar": {"title": "Prevalence (%)"}
                    }
                ],
                "layout": {
                    "title": f"Regional Prevalence of {disease_name}",
                    "geo": {"scope": "usa"}
                }
            }
            
            # Trend over time
            years = [entry["year"] for entry in data["yearly_trend"]]
            regions = data["regions"]
            
            fig2_data = []
            for i, region in enumerate(regions):
                region_values = [entry["percentages"][i] for entry in data["yearly_trend"]]
                fig2_data.append({
                    "x": years,
                    "y": region_values,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": region
                })
                
            fig2 = {
                "data": fig2_data,
                "layout": {
                    "title": f"Prevalence Trend of {disease_name} by Region",
                    "xaxis": {"title": "Year"},
                    "yaxis": {"title": "Prevalence (%)"}
                }
            }
            plots = [fig1, fig2]
            
        else:  # yield_impact
            # Impact on yield
            fig1 = {
                "data": [
                    {
                        "x": data["infection_severity"],
                        "y": data["yield_percentage"],
                        "type": "bar",
                        "marker": {"color": "rgba(255, 100, 100, 0.7)"}
                    }
                ],
                "layout": {
                    "title": f"Yield Impact of {disease_name}",
                    "xaxis": {"title": "Infection Severity"},
                    "yaxis": {"title": "Yield (%)"}
                }
            }
            
            # Quality impact radar chart
            fig2 = {
                "data": [
                    {
                        "type": "scatterpolar",
                        "r": data["quality_impact"],
                        "theta": data["infection_severity"],
                        "fill": "toself"
                    }
                ],
                "layout": {
                    "polar": {
                        "radialaxis": {
                            "visible": True,
                            "range": [0, 5]
                        }
                    },
                    "title": "Quality Impact by Severity Level"
                }
            }
            plots = [fig1, fig2]
        
        return JSONResponse(content={
            "disease": disease_name,
            "visualization_type": viz_type,
            "plots": plots,
            "raw_data": data
        })
        
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
