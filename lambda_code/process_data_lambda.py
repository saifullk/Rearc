import os
import boto3
import pandas as pd
import io
import json
from pandas import json_normalize


def process_data_and_write_results(event, context):
    input_bucket_1 = os.environ["INPUT_BUCKET_1"]
    input_bucket_2 = os.environ["INPUT_BUCKET_2"]
    output_bucket = os.environ["OUTPUT_BUCKET"]
    csv_input = os.environ["CSV_FILE"]
    json_input = os.environ["JSON_FILE"]
    analysis_output = os.environ["ANALYSIS_FILE"]

    # Process data from input_bucket_1 and input_bucket_2 as needed
    # merge data from both buckets and generate results identical to ones in the jupyter notebook

    s3 = boto3.client("s3")

    try:
        # Load the file from S3 into a pandas DataFrame
        csv_object = s3.get_object(Bucket=input_bucket_1, Key=csv_input)
        csv_df = pd.read_csv(csv_object["Body"], sep="\t")
        print("Loaded CSV")

        # Cleanup - Trim whitespaces in column names and string values in csv dataframe
        csv_df.columns = csv_df.columns.str.strip()
        df_obj = csv_df.select_dtypes(["object"])
        csv_df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())

        # Load JSON file into Pandas DataFrame
        json_object = s3.get_object(Bucket=input_bucket_2, Key=json_input)
        json_stream = json_object["Body"].read().decode("utf-8")
        print(f"Loaded JSON Data :  {json_stream}")

        # Parse the JSON data
        json_data = json.loads(json_stream)
        print("Parsed the JSON data")

        data_node = json_data["data"]

        population_df = json_normalize(data_node)
        print("normalized JSON")

        # Cleanup -  Filter the population data for the years [2013, 2018]
        filtered_population_df = population_df[
            (population_df["ID Year"] >= 2013) & (population_df["ID Year"] <= 2018)
        ]
        print("filtered_population_df")

        # 1 Calculate mean and standard deviation of population
        mean_population = filtered_population_df["Population"].mean()
        std_dev_population = filtered_population_df["Population"].std()

        print(f"Mean Population (2013-2018): {mean_population}")
        print(f"Standard Deviation Population (2013-2018): {std_dev_population}")

        # List to store analysis results
        analysis_results = []

        analysis_results.append("Mean Population (2013-2018) : ")
        analysis_results.append(mean_population)

        analysis_results.append("Standard Deviation Population (2013-2018): ")
        analysis_results.append(std_dev_population)

        # 2 Group by series_id and year, calculate the sum of values

        # Filter columns in the time-series DataFrame
        time_series_df = csv_df[["series_id", "year", "period", "value"]]

        # Group by series_id and year, calculate the sum of values
        best_year_df = (
            time_series_df.groupby(["series_id", "year"])["value"].sum().reset_index()
        )

        # Find the year with the maximum sum of values for each series_id
        best_year_df = best_year_df.loc[
            best_year_df.groupby("series_id")["value"].idxmax()
        ]

        analysis_results.append("Best Year for Each Series")
        analysis_results.append(best_year_df)

        print("Best Year for Each Series: \n")
        print(best_year_df)

        # 3 Filter time-series data for series_id = PRS30006032 and period = Q01
        csv_df_new = csv_df[
            (csv_df["series_id"] == "PRS30006032") & (csv_df["period"] == "Q01")
        ]

        # Merge with population data for the same year
        report_df = pd.merge(
            csv_df_new, population_df, left_on="year", right_on="ID Year", how="left"
        )
        print("Report for series_id = PRS30006032 and period = Q01:")
        print(report_df[["series_id", "year", "period", "value", "Population"]])

        report_df = report_df[["series_id", "year", "period", "value", "Population"]]

        analysis_results.append("Report for series_id = PRS30006032 and period = Q01")
        analysis_results.append(report_df)

        print("Results Logged")
        with open("/tmp/" + analysis_output, "w") as f:
            for result in analysis_results:
                f.write(f"{result}\n")

        # Save results to output_bucket
        s3.upload_file("/tmp/" + analysis_output, output_bucket, analysis_output)

        return {
            "statusCode": 200,
            "body": "Data processed and results written to S3 successfully",
        }

    except Exception as e:
        print(f"Error loading file into pandas DataFrame: {str(e)}")
        return "Error loading and processing the file."


if __name__ == "__main__":
    # For local testing
    event = {}
    context = {}
    result = process_data_and_write_results(event, context)
    print(result)
