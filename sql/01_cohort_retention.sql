-- 01. Cohort retention (long format: one row per cohort month x months-since-first-purchase)
-- Table: online_retail_clean (cleaned data loaded by src/05_load_to_mysql.py)
WITH cohort_base AS (
    SELECT `Customer ID`,
           DATE_FORMAT(InvoiceDate, '%Y-%m-01') AS InvoiceMonth,
           MIN(DATE_FORMAT(InvoiceDate, '%Y-%m-01')) OVER (PARTITION BY `Customer ID`) AS CohortMonth
    FROM online_retail_clean
),
cohort_index AS (
    SELECT CohortMonth,
           TIMESTAMPDIFF(MONTH, CohortMonth, InvoiceMonth) AS CohortIndex,
           `Customer ID`
    FROM cohort_base
)
SELECT CohortMonth,
       CohortIndex,
       COUNT(DISTINCT `Customer ID`) AS CustomerCount
FROM cohort_index
GROUP BY CohortMonth, CohortIndex
ORDER BY CohortMonth, CohortIndex;
