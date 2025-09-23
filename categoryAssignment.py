import csv
import pandas as pd
import re

# Define keywords per category for simple classification
keywords = {
    "Food": ["CAFE", "PIZZA", "CHICK", "MOE'S", "TEA", "TASTE", "GRILL", "BBQ", "PHO", "BURGE", "SUSHI", "CHICKEN", "SUBWAY", "E'S", "TOFU", "RAMEN", "TST*", "KITCHEN", "GRAVY", "MKT", "PONKO"],
    "Personal care": ["HAIRCUT", "SALON", "LA FITNESS"],
    "Other": ["ONLINE PAYMENT", "GA TECH POST OFFICE", "COCA COLA", "BLIND VENDORS", "AMAZON", "EBAY", "STEAMGAMES", "WINDSCRIBE", "OPENAI", "WANIKANI", "ZIPCAR", "ZELLE"],
    "Groceries": ["PUBLIX", "7-ELEVEN", "KROGER", "ABC"],
    "Shopping": ["UNIQLO", "SUNGLASS", "PAGES", "TARGET", "B&H PHOTO", "BESTBUY"],
    "Entertainment": ["REG ATLANTIC", "CONNECTIONS", "ESCAPE GAME", "VAIL", "HIGHLAND MUSIC STUDIO"],
    "Fixed Expenses": ["TMOBILE"],
    "Travel": ["LIME", "UBER", "HELE", "DELTA AIR", "FRONTIER AI"],
    "Presents": [],
    "Health": []
}

def classify_transaction(description):
    """Classify a transaction based on keywords in its description."""
    if not isinstance(description, str):
        return "Other"
    
    desc_upper = description.upper()
    for category, keys in keywords.items():
        if any(key in desc_upper for key in keys):
            return category
    return "Other"

def process_transactions(input_file, output_file=None):
    """
    Read transactions from CSV, classify them, and save results.
    If output_file is None, overwrites the input file.
    """
    if output_file is None:
        output_file = input_file
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Ensure required columns exist
    if 'merchant' not in df.columns:
        raise ValueError("CSV file must contain a 'transaction' column")
    
    # Classify each transaction
    df['category'] = df['merchant'].apply(classify_transaction)
    
    # Save the results
    df.to_csv(output_file, index=False)
    print(f"Processed transactions saved to {output_file}")
    return df

def clean_merchant_data(input_file, output_file):
    # Read the CSV file (assuming first row is header)
    df = pd.read_csv(input_file)
    
    # Get the column name for the description column (assuming it's the second column)
    desc_col = df.columns[1]
    
    # Function to extract merchant and state
    def extract_merchant_state(text):
        # Skip if it's a Zelle payment or similar
        if pd.isna(text) or 'Zelle payment' in text or 'INTEREST PAYMENT' in text or 'APPLECARD GSBANK PAYMENT' in text:
            return None, None
        
        # Remove dates (patterns like 06/16, 06/16/23, etc.)
        text = re.sub(r'\s\d{1,2}/\d{1,2}(/\d{2,4})?\s*$', '', text)
        
        # Remove reference numbers, phone numbers, and other patterns
        text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '', text)  # Phone numbers
        text = re.sub(r'\b\d{10,}\b', '', text)  # Long numbers
        text = re.sub(r'\bWEB ID:.*$', '', text)  # Web IDs
        text = re.sub(r'\bYen.*$', '', text)  # Currency conversions
        text = re.sub(r'\bgosq\.com\b', '', text)  # Website references
        
        # Extract state (last 2 letters that match US state abbreviations)
        states = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
                 'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
                 'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
                 'TX','UT','VT','VA','WA','WV','WI','WY']
        
        # Find state in the text
        state = None
        for s in states:
            if f' {s}' in text:
                state = s
                break
        
        # If state found, extract merchant name
        if state:
            merchant = text[:text.rfind(state)].strip()
            # Clean up merchant name
            merchant = re.sub(r'\s+', ' ', merchant)  # Remove extra spaces
            merchant = re.sub(r'^\*', '', merchant)  # Remove leading *
            merchant = re.sub(r'^\w\*', '', merchant)  # Remove patterns like UBR*
            merchant = merchant.strip()
            return merchant, state
        else:
            # For entries without state, try to extract meaningful merchant name
            merchant = re.sub(r'\s+', ' ', text).strip()
            return merchant, None
    
    # Apply the function to the description column
    df[['Merchant', 'State']] = df[desc_col].apply(
        lambda x: pd.Series(extract_merchant_state(x)))
    
    # Drop rows where both Merchant and State are None
    df = df.dropna(subset=['Merchant', 'State'], how='all')
    
    # Save to new CSV file
    df.to_csv(output_file, index=False)
    
    return df


process_transactions('transactions.csv')

#clean_merchant_data('transactions.csv', 'transactions.csv')