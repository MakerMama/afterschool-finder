import pandas as pd
from utils import load_and_process_data

# Test data loading
print("=" * 60)
print("TESTING DATA LOAD")
print("=" * 60)

# Load raw CSV first
df_raw = pd.read_csv('attached_assets/ProgramData.csv')
print(f"\n✓ Raw CSV loaded: {len(df_raw)} programs")
print(f"✓ Columns: {len(df_raw.columns)}")

# Test cost formatting in raw data
print(f"\n--- Cost Data (Raw) ---")
print(f"Sample costs: {df_raw['Cost'].head(10).tolist()}")
print(f"Cost data type: {df_raw['Cost'].dtype}")

# Load with processing
print("\n" + "=" * 60)
print("TESTING PROCESSED DATA")
print("=" * 60)

df = load_and_process_data('attached_assets/ProgramData.csv')
print(f"\n✓ Processed data loaded: {len(df)} programs")

# Test cost after processing
print(f"\n--- Cost Data (Processed) ---")
print(f"Sample costs: {df['Cost'].head(10).tolist()}")
print(f"Cost data type: {df['Cost'].dtype}")
print(f"Min cost: ${df['Cost'].min():.2f}")
print(f"Max cost: ${df['Cost'].max():.2f}")

# Test categories
print(f"\n--- Interest Categories ---")
categories = sorted(df['Interest Category'].dropna().unique())
print(f"Total unique categories: {len(categories)}")
print(f"Categories: {categories[:10]}...")

# Test days
print(f"\n--- Days of Week ---")
days = sorted(df['Day of the week'].unique())
print(f"Days: {days}")

# Test program types
print(f"\n--- Program Types ---")
if 'Program Type' in df.columns:
    prog_types = df['Program Type'].value_counts()
    print(prog_types)

# Test age range
print(f"\n--- Age Range ---")
print(f"Min Age: {df['Min Age'].min()} - Max Age: {df['Max Age'].max()}")

# Test time format
print(f"\n--- Time Format ---")
print(f"Sample start times: {df['Start time'].head(5).tolist()}")
print(f"Sample end times: {df['End time'].head(5).tolist()}")

print("\n" + "=" * 60)
print("DATA VALIDATION COMPLETE")
print("=" * 60)
