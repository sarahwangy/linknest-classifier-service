#!/bin/bash
# 持续负载测试脚本——用来触发Auto Scaling的CPU扩容阈值
# 用法：./load_test.sh <你的SERVICE_API_KEY>
# 会持续跑5分钟，每轮发50个并发请求，中间几乎不停顿

if [ -z "$1" ]; then
  echo "用法: ./load_test.sh <你的SERVICE_API_KEY>"
  exit 1
fi

API_KEY="$1"
URL="http://linknest-alb-516349122.ap-southeast-2.elb.amazonaws.com/classify"
DURATION=300  # 持续5分钟
END_TIME=$((SECONDS + DURATION))

echo "开始持续负载测试，持续${DURATION}秒（5分钟）..."
echo "按Ctrl+C可以提前停止"

ROUND=0
while [ $SECONDS -lt $END_TIME ]; do
  ROUND=$((ROUND + 1))
  echo "第${ROUND}轮，已运行$((SECONDS))秒..."
  for i in {1..50}; do
    curl -s -X POST "$URL" \
      -H "X-API-Key: $API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"title\": \"load test round ${ROUND} item ${i}\"}" > /dev/null &
  done
  wait
done

echo "负载测试结束，共跑了${ROUND}轮"
