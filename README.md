# Ilorin Smart Waste
### Smarter Waste Management, Cleaner Communities



Ilorin Smart Waste is an AI-powered environmental technology prototype exploring how data and artificial intelligence can support better waste identification, reporting, and management in Ilorin, Kwara State, Nigeria.

The project combines a digital waste reporting interface, area-level analysis, and an image classification model to demonstrate how technology can contribute to cleaner and healthier communities.

## The Problem
Improper waste disposal is a persistent environmental concern in many communities. In parts of Ilorin, waste is sometimes discarded in open spaces and drainage channels, contributing to pollution, blocked drainage, and potential public health risks.
Limited access to suitable disposal channels and organised waste information can also make it difficult to identify areas requiring attention.

## The Solution
Ilorin Smart Waste explores a data-driven approach to these challenges through a Streamlit web application.

## Key Features
Waste Management Dashboard: Displays waste report summaries and related records.
Waste Reporting: Allows users to submit waste-related issues by area, waste type, and description.
Area Analysis: Demonstrates how reported information can support area-level analysis and preliminary prioritisation.
AI Waste Classification: Uses a trained image classification model to identify six broad waste categories from uploaded photographs.

## AI Model
The image classification component uses MobileNetV3 Small, fine-tuned with PyTorch and Torchvision.
Dataset: TrashBusters/combined from Hugging Face.
Waste categories:
Cardboard
Glass
Metal
Paper
Plastic
Trash

## Model Performance
Evaluation metric
Result
Training images
20,894
Validation images
4,477
Test images
4,478
Validation accuracy
88.07%
Test accuracy
87.87%
Macro F1-score
0.88
Images are resized to 224 × 224 pixels and normalised before prediction.

Note: These results are based on the model's evaluation dataset. Real-world performance on locally collected Ilorin waste images still requires field validation.


## Technology Stack
Python
Streamlit
Pandas
NumPy
PyTorch
Torchvision
Pillow (PIL)
Git and GitHub

## Project Structure

SMART_WASTE/
│
├── app.py
├── models/
│   ├── ilorin_waste_classifier.pth
│   └── waste_class_names.json
│
├── ilorin_SMART_WASTE.ipynb
├── requirements.txt
├── README.md
└── .gitignore

# Installation and Setup
### 1. Clone the repository
git clone https://github.com/okukunofisat007/SMART_WASTE.git
### 2. Enter the project directory
cd SMART_WASTE
### 3. Create and activate a virtual environment
python -m venv .venv
Windows Command Prompt:
.venv\Scripts\activate.bat
### 4. Install dependencies
python -m pip install -r requirements.txt
For a CPU-only PyTorch installation, if it is not already included in your requirements:
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
### 6. Run the application
streamlit run app.py
The application should open in your browser.
Ensure the trained model files are available in the models directory.

## Limitations
The application currently uses demonstration records rather than verified live municipal data.
The area priority score is preliminary and rule-based, not a trained prediction model.

The image classifier recognises six broad waste categories and may misclassify unfamiliar images.
Organic and hazardous waste do not have dedicated classification categories.

The model has not yet undergone extensive field validation using locally collected images.

## Future Development
Planned improvements include:
Collecting and validating waste reports from communities in Ilorin.
Expanding the image dataset with locally captured waste images.

Adding organic and hazardous waste categories.

Developing waste accumulation trend analysis and forecasting.

Improving location-based prioritisation.

Integrating a persistent database and interactive map.

Exploring collaboration with waste collection organisations.

## Project Background
Ilorin Smart Waste started as a project idea during the Webfala Women in AI Fellowship.
The idea was inspired by personal observations of improper waste disposal and the difficulty of finding suitable disposal channels within the community.
It was developed as a presentation prototype and is now being extended to explore practical applications of AI and data-driven environmental solutions.

## Author
Okuku Nofisat Ohunene
B.Sc. Chemistry | AI Engineer |
Webfala Women in AI Fellowship
GitHub: @okukunofisat007
Repository: Ilorin Smart Waste
