1️⃣ তোমার Spark ও Scala ভার্সন বের করো

pyspark --version


তুমি দেখবে যেমন:

                Welcome to
      Spark version 3.5.0
Scala version 2.12.18


এখান থেকে:

Spark = 3.5.0 → মেজর/মাইনর 3.5.x

Scala = 2.12.x


2️⃣ সঠিক প্যাকেজ নাম ঠিক করো

প্যাকেজ ফরম্যাট:

                org.apache.spark:spark-sql-kafka-0-10_<scala-version>:<spark-version>

তোমার ক্ষেত্রে (Spark 3.5.x, Scala 2.12):

                    org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.6



সঠিকভাবে চালানোর ধাপ

Python shell থেকে বেরিয়ে আসো (Ctrl + Z অথবা exit() লিখে)।

তারপর তোমার টার্মিনাল/কমান্ড প্রম্পটে চালাও:

pyspark --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.6


যদি Python স্ক্রিপ্ট রান করাতে চাও

টার্মিনাল থেকে: 

spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.6 streaming_job.py


localhost:4040
