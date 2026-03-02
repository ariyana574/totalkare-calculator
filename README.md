# TotalKare Service Contract Calculator

Professional service contract calculator and admin portal for TotalKare.

## Features

- **Vehicle Lift Contracts:** Standard, Extra, Fixed Labour, PRO-2 Warranty
- **Brake Tester Contracts:** Full service with calibrations
- **Multi-Equipment Support:** Combine multiple items in one contract
- **Add-ons & Ancillary:** Battery plans, lube pots, ancillary equipment
- **Dynamic Pricing:** Old (2023/24) vs New (2025) pricing
- **Admin Dashboard:** Live price management via Google Sheets
- **Island Restrictions:** Automatic handling for Shetlands, Isle of Man, etc.

## Usage

### Main Calculator
- Select equipment type (Lifts or Brake Testers)
- Upload NetSuite CSV with customer data
- Select customer and equipment
- Configure contract options
- Review and generate quote

### Admin Portal
- Access via sidebar navigation
- Edit pricing tables in real-time
- Add new ancillary equipment
- Changes sync to Google Sheets

## Tech Stack

- **Frontend:** Streamlit
- **Data Storage:** Google Sheets API
- **Authentication:** OAuth2 Service Account
- **Deployment:** Streamlit Community Cloud

## Local Development
```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Deployment

Deployed on Streamlit Community Cloud with Google Sheets backend.