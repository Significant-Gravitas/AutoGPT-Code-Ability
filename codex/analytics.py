import numpy as np
import pandas as pd
import prisma


async def get_template_performance():
    db = prisma.Prisma(auto_register=True)

    await db.connect()
    # Load the data from the database
    templates = await prisma.models.LLMCallTemplate.prisma().find_many()
    template_data = pd.DataFrame([d.model_dump() for d in templates])

    calls = await prisma.models.LLMCallAttempt.prisma().find_many()
    calls_data = pd.DataFrame([d.model_dump() for d in calls])
    joined_data = calls_data.merge(
        template_data, how="inner", left_on="llmCallTemplateId", right_on="id"
    )
    # Group by 'templateName' and 'fileHash'
    grouped = joined_data.groupby(["templateName", "fileHash"])

    # Define a function to count occurrences of 'attempt' values within the desired range
    def count_attempts(data, val):
        return np.sum(data == val)

    # Perform aggregation
    result = grouped.agg(
        total_count=("templateName", "size"),  # Count of rows
        first_call_count=(
            "firstCallId",
            lambda x: x.isnull().sum(),
        ),  # Count of rows where 'firstCallId' is not None
        template_created_at=("createdAt_y", "max"),  # Latest 'createdAt_y'
        max_retry_count=("attempt", "max"),  # Maximum 'retryCount'
        # **{f'attempt_{i}_count': ('attempt', lambda x, i=i: count_attempts(x, i)) for i in range(11)} #type: ignore
    )
    result["pass_rate"] = result["first_call_count"] / result["total_count"]
    result = result[result["pass_rate"] < 1]

    # Calculate the standard error (SE) for the pass rate
    result["pass_rate_SE"] = np.sqrt(
        (result["pass_rate"]) * (1 - (result["pass_rate"])) / result["total_count"]
    )

    # If you need the margin of error for a 95% confidence interval, you can multiply the SE by 1.96
    result["pass_rate_margin_of_error"] = 1.96 * result["pass_rate_SE"]

    # To convert the margin of error back to percentage form, you might multiply by 100 if needed
    result["error_bars"] = result["pass_rate_margin_of_error"] * 100

    result["pass_rate"] = result["pass_rate"] * 100

    # Sort the result DataFrame by 'templateName' and 'template_created_at'
    result_sorted = result.sort_values(
        by=["templateName", "template_created_at"]
    ).reset_index()

    # Define a new column for the assessment in the sorted DataFrame
    result_sorted["Assessment"] = None  # Initialize with None

    # Temporary storage for the previous row's pass rate and error bars by template
    prev_pass_rate = {}
    prev_error_bar = {}

    # Iterate through each row in the sorted DataFrame
    for index, row in result_sorted.iterrows():
        template_name = row["templateName"]
        if template_name in prev_pass_rate:
            # Calculate the difference in pass rates and consider the error bars
            diff = row["pass_rate"] - prev_pass_rate[template_name]
            error_margin = row["error_bars"] + prev_error_bar[template_name]

            # Assess the difference
            if diff > error_margin:
                assessment = "Improving"
            elif diff < -error_margin:
                assessment = "Degrading"
            elif diff > 0:
                assessment = "Possibly Improving"
            elif diff < 0:
                assessment = "Possibly Degrading"
            else:
                assessment = "No significant change"

            result_sorted.at[index, "Assessment"] = assessment
        else:
            # This is the first entry for this templateName; no comparison possible
            result_sorted.at[index, "Assessment"] = "Initial Entry"

        # Update the previous values for comparison in the next iteration
        prev_pass_rate[template_name] = row["pass_rate"]
        prev_error_bar[template_name] = row["error_bars"]

    # Sort back if needed or perform additional operations
    # Truncate 'fileHash' to 8 characters
    result_sorted["fileHash"] = result_sorted["fileHash"].apply(lambda x: x[:8])

    # Format 'template_created_at' without fractions of a second or timezone
    result_sorted["template_created_at"] = pd.to_datetime(
        result_sorted["template_created_at"]
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    columns_ordered = [
        "template_created_at",
        "templateName",
        "pass_rate",
        "error_bars",
        "max_retry_count",
        "Assessment",
    ]
    result_sorted = result_sorted[columns_ordered]
    print(result_sorted)
    await db.disconnect()

    # Return the updated DataFrame
    return result_sorted

    # After all previous operations including adding 'pass_rate'

    # Reorder the DataFrame according to the new column order
    result = result[columns_ordered]

    print(result)

    await db.disconnect()
    return joined_data
