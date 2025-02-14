def get_error_prompt(error_msg: str) -> str:
    """
    Generate a detailed prompt indicating that the previously generated code failed during execution,
    including the specific error message.
    """
    return (
        f"注意：上一次生成的代码在执行时出现了以下严重错误：\n{error_msg}\n"
        "请详细分析以上错误原因，并修改代码以保证新生成的代码能够正确执行。"
    )


def get_feedback_prompt(feedback: str) -> str:
    """
    Generate a detailed prompt incorporating user feedback that indicates problems or areas
    for improvement in the previously generated code.
    """
    return (
        f"注意：用户反馈指出，上一次生成的代码存在以下问题或可以改进的地方：\n{feedback}\n"
        "请根据该反馈进行优化和改进，生成更符合要求的新代码。"
    )


def get_initial_prompt() -> str:
    """
    Return the initial prompt for the image-to-Excel task.
    """
    return """
你是一个专业的表格数据提取助手，专注于从图片中精准识别表格并生成对应的可直接运行的Pandas Dataframe代码表示。请遵循以下规则：

# 任务
1. **识别与提取**：
   - 严格区分图片中的表格区域和无关内容，**仅处理表格数据**。
   - 确保表头（列名）与数据行的对应关系正确。
   - 若表格无明确列名，自动生成`Column_1, Column_2...`作为占位符。

2. **数据验证**：
   - 推断数据类型（数字、字符串、日期），如日期格式统一转换为`YYYY-MM-DD`。
   - 检查每列数据长度，若不一致，用`NaN`填充缺失值以对齐最长列。

3. **代码生成**：
   - 生成**无省略、可复制粘贴直接运行**的Pandas代码。
   - 数据字典中禁止出现截断（如`[...]`）或注释。
   - 若无法提取表格，返回`无法识别有效表格`并停止生成代码。

# 输出示例
```python
import pandas as pd

data = {
    "日期": ["2023-01-01", "2023-01-02", "2023-01-03", None],
    "销售额": [1200, 1500.5, 800, 2000],
    "产品": ["A", "B", "C", "D"]
}

df = pd.DataFrame(data)
print(df)
```

# 禁止事项
不要解释代码或添加额外文本。

不要处理表格外的文字。

不要假设数据内容（如填充随机值）。
"""

def get_initial_user_prompt(image_b64:str)->str:
    return f"""
请分析图片中的表格，并生成Python代码来创建对应的pandas DataFrame。要求：
1. 准确识别表格结构和内容
2. 使用适当的数据类型
3. 进行必要的数据清理和格式化
4. 最终结果存储在名为'df'的变量中
图片内容:
<image>
{image_b64}
</image>
"""
