CREATE OR REPLACE VIEW view.user_first_orders
OPTIONS (description="ユーザー情報に最初に注文した日時の情報を付け加えたテーブル", labels=[("git", "true")]) AS

WITH first_order_each_users AS (

SELECT
  user_id,
  MIN(created) AS created
FROM your_dataset.orders
GROUP BY user_id 

)

SELECT
  u.*,
  o.created AS first_ordered
FROM your_dataset.users u
LEFT JOIN first_order_each_users o
ON u.id = o.user_id