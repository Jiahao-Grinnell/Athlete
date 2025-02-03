import pandas as pd

# Paths to your two Excel files
men_file = "Men Team Expenses.xlsx"
women_file = "Women Team Expenses.xlsx"

# Read each file into a DataFrame
df_men = pd.read_excel(men_file)
df_women = pd.read_excel(women_file)

# Melt each DataFrame from wide to long:
#  - "Year" is kept as is (id_vars)
#  - each sport column becomes a row under "Sport"
#  - the values go into the "Cost" column
df_men_melted = df_men.melt(id_vars="Year", var_name="Sport", value_name="Cost")
df_women_melted = df_women.melt(id_vars="Year", var_name="Sport", value_name="Cost")

# Add a "Gender" column to each
df_men_melted["Gender"] = "Men"
df_women_melted["Gender"] = "Women"

# Combine both melted DataFrames
combined_df = pd.concat([df_men_melted, df_women_melted], ignore_index=True)

# Rearrange columns if you prefer a specific order:
combined_df = combined_df[["Year", "Sport", "Cost", "Gender"]]

# Save the result to Excel (or CSV)
combined_df.to_excel("Combined_Team_Expenses.xlsx", index=False)
# If you prefer CSV:
# combined_df.to_csv("Combined_Team_Expenses.csv", index=False)

print("Combined file created successfully!")
