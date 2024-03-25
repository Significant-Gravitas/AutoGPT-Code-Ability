import click
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


async def get_costs():
    db = prisma.Prisma(auto_register=True)
    await db.connect()

    templates = await prisma.models.LLMCallTemplate.prisma().find_many()
    template_data = pd.DataFrame([d.model_dump() for d in templates])

    calls = await prisma.models.LLMCallAttempt.prisma().find_many()
    calls_data = pd.DataFrame([d.model_dump() for d in calls])

    # Merge calls with templates
    result = calls_data.merge(
        template_data, how="inner", left_on="llmCallTemplateId", right_on="id"
    )
    retries_result = result[result["attempt"] > 0]

    # Calculate total cost
    per_app = result.groupby(["applicationId", "developmentPhase"])[
        ["completionTokens", "promptTokens"]
    ].sum()
    # Adjusted section for calculating total cost
    per_app = per_app.assign(
        completionCost=per_app["completionTokens"] * 30 / 1_000_000,
        promptCost=per_app["promptTokens"] * 10 / 1_000_000,
    )
    per_app["total_cost"] = per_app["completionCost"] + per_app["promptCost"]

    per_app = per_app.reset_index()
    median_costs_by_phase = per_app.groupby("developmentPhase")["total_cost"].median()
    dev_cost = median_costs_by_phase.get(
        "DEVELOPMENT", 0
    )  # Default to 0 if not present
    req_cost = median_costs_by_phase.get("REQUIREMENTS", 0)
    per_app_cost = (
        per_app[["applicationId", "total_cost"]]
        .groupby("applicationId")
        .sum()
        .median()
        .get("total_cost", 0)
    )

    # # Calculate retries cost
    retries_result = (
        retries_result[["applicationId", "completionTokens", "promptTokens"]]
        .groupby(["applicationId"])
        .sum()
    )
    retries_cost = retries_result.assign(
        completionCost=retries_result["completionTokens"] * 30 / 1_000_000,
        promptCost=retries_result["promptTokens"] * 10 / 1_000_000,
    )
    retries_cost["total_cost"] = (
        retries_cost["completionCost"] + retries_cost["promptCost"]
    )

    retries_cost = retries_cost["total_cost"].median()

    retries_percentage = (retries_cost / per_app_cost) * 100

    await db.disconnect()

    output_message = f"""
Median cost per app: {click.style(f'${per_app_cost:.2f}', fg='green', bold=True)}

Median Requirements phase cost: {click.style(f'${req_cost:.2f}', fg='blue', bold=True)}
Median Development phase cost: {click.style(f'${dev_cost:.2f}', fg='blue', bold=True)}

Median Cost due to retries: {click.style(f'${retries_cost:.2f}', fg='red', bold=True)} = {click.style(f'{retries_percentage:.0f}%', fg='red', bold=True)} of cost is due to needing to retry
"""

    click.echo(output_message)
