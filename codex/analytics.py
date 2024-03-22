import numpy as np
import pandas as pd
import prisma


async def get_template_performance() -> pd.DataFrame:
    """
    Retrieves template performance data from the database and performs aggregation and analysis.

    Returns:
        pandas.DataFrame: The updated DataFrame containing template performance data.
    """
    db = prisma.Prisma(auto_register=True)

    await db.connect()
    templates = await prisma.models.LLMCallTemplate.prisma().find_many()
    template_data = pd.DataFrame([d.model_dump() for d in templates])

    calls = await prisma.models.LLMCallAttempt.prisma().find_many()
    calls_data = pd.DataFrame([d.model_dump() for d in calls])

    result = (
        calls_data.merge(
            template_data, how="inner", left_on="llmCallTemplateId", right_on="id"
        )
        .groupby(["templateName", "fileHash"])
        .agg(
            total_count=("templateName", "size"),  # Count of rows
            first_call_count=(
                "firstCallId",
                lambda x: x.isnull().sum(),
            ),  # Count of rows where 'firstCallId' is not None
            template_created_at=("createdAt_y", "max"),  # Latest 'createdAt_y'
            max_retry_count=("attempt", "max"),  # Maximum 'retryCount'
            # **{f'attempt_{i}_count': ('attempt', lambda x, i=i: count_attempts(x, i)) for i in range(11)} #type: ignore
        )
    )
    result["pass_rate"] = result["first_call_count"] / result["total_count"]

    result = result[result.groupby(["templateName"])["pass_rate"].transform("min") < 1]
    result = result.assign(
        error_bars=2
        * np.sqrt(
            (result["pass_rate"]) * (1 - (result["pass_rate"])) / result["total_count"]
        )
        * 100,
        pass_rate=result["pass_rate"] * 100,
        Assessment=None,
    )

    result = result.sort_values(
        by=["templateName", "template_created_at"]
    ).reset_index()

    prev_pass_rate = {}
    prev_error_bar = {}

    for index, row in result.iterrows():
        template_name = row["templateName"]
        if template_name in prev_pass_rate:
            diff = row["pass_rate"] - prev_pass_rate[template_name]
            error_margin = row["error_bars"] + prev_error_bar[template_name]

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

            result.at[index, "Assessment"] = assessment
        else:
            result.at[index, "Assessment"] = "Initial Entry"

        prev_pass_rate[template_name] = row["pass_rate"]
        prev_error_bar[template_name] = row["error_bars"]

    result = result.assign(
        fileHash=result["fileHash"].apply(lambda x: x[:8]),
        template_created_at=pd.to_datetime(result["template_created_at"]).dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

    columns_ordered = [
        "template_created_at",
        "templateName",
        "pass_rate",
        "error_bars",
        "max_retry_count",
        "Assessment",
    ]
    result = result[columns_ordered]
    print(result)
    await db.disconnect()

    return result
