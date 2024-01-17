@echo
chcp 65001
python .\main.py "SELECT top 1 '09174666040'as phone , N'سلام' as msg FROM [AdventureWorks].[Person].[Person]"
