import os
import json
import uuid
import tempfile
from datetime import datetime
from typing import Tuple

import gradio as gr
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def call_gemini_api(prompt: str) -> str:
    """
    Calls the Google Gemini API with a static prompt to generate a mock scan report.
    
    Args:
        prompt: The prompt to send to Gemini
    
    Returns:
        Generated text response from Gemini
    """
    try:
        # Initialize the Gemini model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Generate content
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        # Return a fallback response if API call fails
        return f"""SUMMARY
This is a mock security scan report generated as a fallback. The system encountered an API issue: {str(e)}

FINDINGS
- No critical vulnerabilities detected in fallback mode
- System appears to be functioning within normal parameters
- Recommend running actual scan when API connectivity is restored

RECOMMENDATIONS  
- Verify API configuration and connectivity
- Re-run scan with proper API access
- Implement monitoring for API availability"""

def parse_report_sections(report_text: str) -> dict:
    """
    Parses the Gemini response into structured sections.
    
    Args:
        report_text: Raw text from Gemini API
    
    Returns:
        Dictionary with parsed sections
    """
    # Convert to uppercase for consistent parsing
    text_upper = report_text.upper()
    
    # Find section boundaries
    summary_start = text_upper.find('SUMMARY')
    findings_start = text_upper.find('FINDINGS')
    recommendations_start = text_upper.find('RECOMMENDATIONS')
    
    # Extract sections with fallback handling
    if summary_start != -1:
        summary_end = findings_start if findings_start != -1 else len(report_text)
        summary = report_text[summary_start + 7:summary_end].strip()
    else:
        summary = "No summary section found in the generated report."
    
    if findings_start != -1:
        findings_end = recommendations_start if recommendations_start != -1 else len(report_text)
        findings = report_text[findings_start + 8:findings_end].strip()
    else:
        findings = "No findings section found in the generated report."
    
    if recommendations_start != -1:
        recommendations = report_text[recommendations_start + 13:].strip()
    else:
        recommendations = "No recommendations section found in the generated report."
    
    return {
        'summary': summary,
        'findings': findings,
        'recommendations': recommendations
    }

def create_pdf_report(report_data: dict) -> str:
    """
    Creates a PDF report from the parsed report data and saves it to a temporary file.
    
    Args:
        report_data: Dictionary containing report sections
    
    Returns:
        Path to the temporary PDF file
    """
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_file.close()
    
    # Create the PDF document
    doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor='darkblue'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor='darkred'
    )
    
    # Build the PDF content
    story = []
    
    # Title
    story.append(Paragraph("Mock Security Scan Report", title_style))
    story.append(Spacer(1, 20))
    
    # Date
    current_date = datetime.now().strftime("%Y-%m-%d")
    story.append(Paragraph(f"<b>Date:</b> {current_date}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Summary section
    story.append(Paragraph("SUMMARY", heading_style))
    story.append(Paragraph(report_data['summary'], styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Findings section
    story.append(Paragraph("FINDINGS", heading_style))
    story.append(Paragraph(report_data['findings'], styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Recommendations section
    story.append(Paragraph("RECOMMENDATIONS", heading_style))
    story.append(Paragraph(report_data['recommendations'], styles['Normal']))
    
    # Build the PDF
    doc.build(story)
    
    return temp_file.name

def create_json_report(report_data: dict) -> str:
    """
    Creates a JSON report from the parsed report data and saves it to a temporary file.
    
    Args:
        report_data: Dictionary containing report sections
    
    Returns:
        Path to the temporary JSON file
    """
    # Create the JSON structure
    json_data = {
        "report_id": str(uuid.uuid4()),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "summary": report_data['summary'],
        "findings": report_data['findings'],
        "recommendations": report_data['recommendations']
    }
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
    
    # Write JSON data
    json.dump(json_data, temp_file, indent=2, ensure_ascii=False)
    temp_file.close()
    
    return temp_file.name

def run_scan() -> Tuple[str, str]:
    """
    Main function that orchestrates the scan process:
    1. Calls Gemini API to generate report
    2. Creates PDF version
    3. Creates JSON version
    4. Returns both file paths
    
    Returns:
        Tuple of (pdf_file_path, json_file_path)
    """
    # Static prompt for Gemini
    prompt = """Generate a realistic mock security scan report for a web application. 
    The report should include three main sections:
    
    SUMMARY: A brief overview of the scan results and overall security posture
    FINDINGS: Detailed list of security vulnerabilities found, including severity levels
    RECOMMENDATIONS: Specific actionable steps to address the identified issues
    
    Make it realistic but clearly indicate it's a mock/test report. Include technical details like CVE numbers, ports, and specific vulnerability types."""
    
    try:
        print("🔄 Starting scan...")
        
        # Step 1: Call Gemini API
        print("📡 Calling Gemini API...")
        report_text = call_gemini_api(prompt)
        print("✅ Report generated successfully")
        
        # Step 2: Parse the response into sections
        print("📝 Parsing report sections...")
        report_data = parse_report_sections(report_text)
        
        # Step 3: Create PDF report
        print("📄 Creating PDF report...")
        pdf_path = create_pdf_report(report_data)
        print(f"✅ PDF created: {pdf_path}")
        
        # Step 4: Create JSON report  
        print("📊 Creating JSON report...")
        json_path = create_json_report(report_data)
        print(f"✅ JSON created: {json_path}")
        
        print("🎉 Scan completed successfully!")
        
        # Return file paths
        return pdf_path, json_path
        
    except Exception as e:
        print(f"❌ Error during scan: {str(e)}")
        
        # Create error report if something goes wrong
        error_data = {
            'summary': f"Error occurred during scan: {str(e)}",
            'findings': "Unable to complete security scan due to technical issues.",
            'recommendations': "Please check system configuration and try again."
        }
        
        error_pdf = create_pdf_report(error_data)
        error_json = create_json_report(error_data)
        
        return error_pdf, error_json

# Create the Gradio interface
def create_interface():
    """
    Creates and configures the Gradio interface.
    """
    with gr.Blocks(title="Security Scan Report Generator", theme=gr.themes.Soft()) as iface:
        gr.Markdown("# 🔒 Mock Security Scan Report Generator")
        gr.Markdown("Click the **Scan** button to generate a mock security scan report using AI.")
        
        # Status display
        status_display = gr.Markdown("Ready to scan...", elem_id="status")
        
        with gr.Row():
            scan_button = gr.Button("🔍 Start Scan", variant="primary", size="lg")
        
        with gr.Row():
            with gr.Column():
                pdf_download = gr.DownloadButton(
                    label="📄 Download PDF Report",
                    visible=False,
                    variant="secondary"
                )
            
            with gr.Column():
                json_download = gr.DownloadButton(
                    label="📊 Download JSON Data", 
                    visible=False,
                    variant="secondary"
                )
        
        # Define the scan workflow
        def handle_scan():
            """
            Handles the scan button click and shows download options.
            """
            try:
                # Update status
                yield (
                    gr.Markdown("🔄 Scanning in progress..."),
                    gr.DownloadButton(visible=False),
                    gr.DownloadButton(visible=False)
                )
                
                # Run the scan
                pdf_path, json_path = run_scan()
                
                # Return final state with download buttons
                yield (
                    gr.Markdown("✅ Scan completed! Download your reports below:"),
                    gr.DownloadButton(label="📄 Download PDF Report", value=pdf_path, visible=True),
                    gr.DownloadButton(label="📊 Download JSON Data", value=json_path, visible=True)
                )
                
            except Exception as e:
                yield (
                    gr.Markdown(f"❌ Error during scan: {str(e)}"),
                    gr.DownloadButton(visible=False),
                    gr.DownloadButton(visible=False)
                )
        
        # Wire up the button
        scan_button.click(
            fn=handle_scan,
            outputs=[status_display, pdf_download, json_download]
        )
        
        gr.Markdown("---")
        gr.Markdown("**Note:** This generates mock reports for testing purposes only.")
        gr.Markdown("**API Status:** " + ("✅ Gemini API configured" if os.getenv('GEMINI_API_KEY') else "⚠️ No API key - using fallback responses"))
    
    return iface

if __name__ == "__main__":
    # Check for API key
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  Warning: GEMINI_API_KEY not found in environment variables.")
        print("   Create a .env file with: GEMINI_API_KEY=your_api_key_here")
        print("   The app will still run but will use fallback responses.")
    
    print("🚀 Starting Gradio Security Scan Report Generator...")
    
    # Create and launch the interface
    app = create_interface()
    app.launch(
        share=False,  # Set to True if you want a public link
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True  # Show errors in the interface
    )