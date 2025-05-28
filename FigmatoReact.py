import logging
import streamlit as st
import os
import zipfile
import io
import tempfile
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="🖼️ Figma to React Converter", page_icon="⚛️")

# ----------------- AI CODE GENERATION -----------------
def generate_react_code(figma_url, design_description, api_key):
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert React developer. Convert Figma designs into React JS + Tailwind CSS code.
                    Follow these rules:
                    1. Use functional components.
                    2. Use Tailwind for styling (no CSS files).
                    3. Structure components logically (Header, Main, Footer, etc.).
                    4. Return files in this format:
                    
                    # FILE: src/App.js
                    ```jsx
                    // React code here
                    ```
                    
                    # FILE: src/components/Button.js
                    ```jsx
                    // Button component here
                    ```
                    """
                },
                {
                    "role": "user",
                    "content": f"""**Figma URL**: {figma_url}
                    **Design Description**: {design_description}
                    
                    Generate React code for this design. Include:
                    - Proper folder structure
                    - All necessary components
                    - Tailwind CSS styling
                    - Responsive layout if needed"""
                }
            ],
            max_tokens=4000
        )
        
        if response:
            return response.choices[0].message.content
        return None
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        return None

def create_zip_file(code_response):
    files = {}
    current_file = None
    current_content = []
    
    for line in code_response.split('\n'):
        if line.startswith('# FILE: '):
            if current_file:
                files[current_file] = '\n'.join(current_content).strip()
            current_file = line[8:].strip()
            current_content = []
        elif current_file:
            current_content.append(line)
    
    if current_file:
        files[current_file] = '\n'.join(current_content).strip()
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add package.json
        package_json = {
            "name": "figma-to-react",
            "version": "1.0.0",
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1",
                "tailwindcss": "^3.3.0"
            }
        }
        zipf.writestr("package.json", str(package_json))
        
        # Add Tailwind config (if not provided)
        if "tailwind.config.js" not in files:
            tailwind_config = """module.exports = {
                content: ["./src/**/*.{js,jsx}"],
                theme: { extend: {} },
                plugins: []
            }"""
            zipf.writestr("tailwind.config.js", tailwind_config)
        
        # Add all parsed files
        for file_path, content in files.items():
            content = content.replace('```jsx', '').replace('```', '').strip()
            zipf.writestr(file_path, content)
    
    zip_buffer.seek(0)
    return zip_buffer

# ----------------- STREAMLIT UI -----------------
st.title("🖼️ Figma to React Converter")

# Sidebar for API key
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter DeepSeek API Key:", type="password")

# Main UI
st.subheader("Step 1: Provide Figma Design Details")
figma_url = st.text_input("Figma Design URL (Optional)", placeholder="https://figma.com/design/...")
design_description = st.text_area(
    "Describe the Figma Design (Required)", 
    height=200,
    placeholder="""Example:
    - A login page with email/password fields
    - A 'Sign In' button with blue gradient
    - Dark theme with rounded corners
    - Uses Inter font"""
)

if st.button("Generate React Code"):
    if not api_key:
        st.error("Please enter your DeepSeek API key.")
    elif not design_description:
        st.error("Please describe the Figma design.")
    else:
        with st.spinner("Generating React code..."):
            react_code = generate_react_code(figma_url, design_description, api_key)
            
            if react_code:
                st.success("Done! 🎉")
                with st.expander("View Generated Code"):
                    st.code(react_code)
                
                zip_buffer = create_zip_file(react_code)
                st.download_button(
                    label="Download as ZIP",
                    data=zip_buffer,
                    file_name="react-project.zip",
                    mime="application/zip"
                )
            else:
                st.error("Failed to generate code. Check your API key or try again.")

# Info section
st.sidebar.markdown("### How to Use")
st.sidebar.write("""
1. Enter your **DeepSeek API Key**.
2. Paste the **Figma URL** (optional).
3. **Describe** the design (colors, layout, components).
4. Click **Generate React Code**.
""")