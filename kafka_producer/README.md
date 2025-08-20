Required Commands:

.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

.\bin\windows\kafka-server-start.bat .\config\server.properties

kafka-topics.bat --create --bootstrap-server localhost:9092 --replication-factor 1 --partition 1 --topic kap

kafka-console-producer.bat --broker-list localhost:9092 --topic kap


-------------------------------------------------------------------------------------------------------
Sample Data:

{"Name: "John", "Age":"31", "Gender":"Male"}
{"Name: "Emma", "Age":"27", "Gender":"Female"}
{"Name: "Ronald", "Age":"17", "Gender":"Male"}
---------------------------------------------------------------------------------------------------------

kafka-console-consumer.bat --topic kap --bootstrap-server localhost:9092 --from-beginning


.\bin\windows\zookeeper-server-stop.bat .\config\zookeeper.properties

.\bin\windows\kafka-server-stop.bat .\config\server.properties

--------------------------------------------------------------------------------------------------------