"""Spark Structured Streaming ETL reference job.

Run in a Spark image with the package mounted and Kafka connector configured.
"""

import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

EVENT_SCHEMA = T.StructType(
    [
        T.StructField("transaction_id", T.StringType(), False),
        T.StructField("customer_id", T.StringType(), False),
        T.StructField("event_time", T.TimestampType(), False),
        T.StructField("amount", T.DoubleType(), False),
        T.StructField("currency", T.StringType(), False),
        T.StructField("merchant_category", T.StringType(), False),
        T.StructField("country", T.StringType(), False),
        T.StructField("device_trust_score", T.DoubleType(), False),
        T.StructField("account_age_days", T.IntegerType(), False),
        T.StructField("is_new_device", T.BooleanType(), False),
        T.StructField("velocity_1h", T.IntegerType(), False),
        T.StructField("distance_km", T.DoubleType(), False),
        T.StructField("chargeback_history", T.IntegerType(), False),
        T.StructField("is_fraud", T.IntegerType(), True),
    ]
)


def build_stream(
    spark: SparkSession, kafka_bootstrap: str, topic: str, checkpoint: str, output: str
):
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .load()
    )
    events = (
        raw.select(F.from_json(F.col("value").cast("string"), EVENT_SCHEMA).alias("event"))
        .filter(F.col("event").isNotNull())
        .select("event.*")
    )
    valid = (
        events.withWatermark("event_time", "10 minutes")
        .filter(
            (F.col("amount") > 0)
            & (F.col("device_trust_score").between(0, 1))
            & (F.col("account_age_days") >= 0)
            & (F.col("velocity_1h") >= 0)
            & (F.col("distance_km") >= 0)
            & (F.col("chargeback_history") >= 0)
        )
        .withColumn("amount_log", F.log1p("amount"))
        .withColumn("event_date", F.to_date("event_time"))
    )
    return (
        valid.writeStream.format("parquet")
        .option("checkpointLocation", checkpoint)
        .partitionBy("event_date")
        .outputMode("append")
        .start(output)
    )


def required_environment(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


if __name__ == "__main__":
    spark_session = SparkSession.builder.appName("sentinelflow-transaction-etl").getOrCreate()
    query = build_stream(
        spark_session,
        kafka_bootstrap=required_environment("KAFKA_BOOTSTRAP_SERVERS"),
        topic=os.getenv("KAFKA_TOPIC", "transactions"),
        checkpoint=os.getenv(
            "SENTINELFLOW_SPARK_CHECKPOINT",
            "/opt/sentinelflow/checkpoints/transactions",
        ),
        output=os.getenv(
            "SENTINELFLOW_SPARK_OUTPUT",
            "/opt/sentinelflow/data/processed/transactions",
        ),
    )
    query.awaitTermination()
