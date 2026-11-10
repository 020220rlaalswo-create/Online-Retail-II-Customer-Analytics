-- 03. Segment summary: size, averages, revenue and revenue share
SELECT Segment,
       COUNT(*)                                                         AS Customer_Count,
       ROUND(AVG(Recency), 1)                                           AS Avg_Recency,
       ROUND(AVG(Frequency), 1)                                         AS Avg_Frequency,
       ROUND(AVG(Monetary), 1)                                          AS Avg_Monetary,
       ROUND(SUM(Monetary), 1)                                          AS Total_Revenue,
       ROUND(SUM(Monetary) / SUM(SUM(Monetary)) OVER () * 100, 1)       AS Revenue_Share_Pct
FROM customer_rfm
GROUP BY Segment
ORDER BY Total_Revenue DESC;
