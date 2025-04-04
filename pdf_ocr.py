import os
import glob
import json
import subprocess

def run_ocr_pipeline():
    # Define the workspace and pdf directory pattern.
    workspace = "./localworkspace"
    pdf_pattern = "./test_pdfs/*.pdf"

    # Expand the glob pattern so that you get a list of PDF file paths.
    pdf_files = glob.glob(pdf_pattern)
    if not pdf_files:
        print("No PDF files found in", pdf_pattern)
        return

    # Build the command. Here we pass each PDF file as an individual argument.
    cmd = ["python", "-m", "olmocr.pipeline", workspace, "--pdfs"] + pdf_files

    print("Running OCR pipeline command:")
    print(" ".join(cmd))
    
    # Run the OCR command and wait for it to complete.
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if process.returncode != 0:
        print("OCR pipeline encountered an error:")
        print(process.stderr)
    else:
        print("OCR pipeline finished successfully.")
        
def convert_jsonl_to_markdown(results_dir="./localworkspace/results", output_dir="./test_pdfs_md"):
    # Create the output directory if it doesn't exist.
    os.makedirs(output_dir, exist_ok=True)
    
    # Look for all .jsonl files in the results directory.
    jsonl_files = glob.glob(os.path.join(results_dir, "*.jsonl"))
    
    if not jsonl_files:
        print("No JSONL files found in", results_dir)
        return
    
    for jsonl_file in jsonl_files:
        print(f"Processing {jsonl_file}...")
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file {jsonl_file}: {e}")
                    continue
                
                # Get the source file name from metadata. If not present, use the id.
                metadata = doc.get("metadata", {})
                source_file = metadata.get("Source-File", doc.get("id", "unknown"))
                # Remove any path components and change the extension to .md
                base_name = os.path.basename(source_file)
                name_without_ext, _ = os.path.splitext(base_name)
                markdown_filename = os.path.join(output_dir, f"{name_without_ext}.md")
                
                # Prepare Markdown content: the source file name as a header and the OCR text below.
                ocr_text = doc.get("text", "")
                markdown_content = f"# {base_name}\n\n" + ocr_text
                
                # Write to the Markdown file.
                with open(markdown_filename, "w", encoding="utf-8") as md_file:
                    md_file.write(markdown_content)
                
                print(f"Created markdown: {markdown_filename}")

def main():
    # Step 1: Run the OCR pipeline.
    run_ocr_pipeline()
    
    # Step 2: Convert JSONL results to Markdown.
    convert_jsonl_to_markdown()

if __name__ == "__main__":
    main()
