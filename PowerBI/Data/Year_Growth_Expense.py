import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('all_school_expenses.csv')

# Sort the DataFrame to ensure proper ordering for each school, sport, and gender.
df.sort_values(by=['School', 'Sport', 'Gender', 'Year'], inplace=True)

# Compute Accumulative Growth:
# For each group (School, Sport, and Gender), use the 2003 expense as the base (i.e., 1),
# then compute each year's expense relative to the 2003 expense.
df['Accumulative Growth'] = df.groupby(['School', 'Sport', 'Gender'])['Expense'] \
    .transform(lambda x: x / x.iloc[0])

# Compute Yearly Change:
# For each group, calculate the difference between this year's expense and the previous year's,
# then divide that difference by the previous year's expense.
df['Yearly Change'] = df.groupby(['School', 'Sport', 'Gender'])['Expense'] \
    .transform(lambda x: x.diff() / x.shift(1))

# For the base year (2003), set the Yearly Change to 0 since there is no previous year.
df.loc[df['Year'] == 2003, 'Yearly Change'] = 0

# Save the updated DataFrame to a new CSV file locally.
df.to_csv('all_school_expenses_updated.csv', index=False)
