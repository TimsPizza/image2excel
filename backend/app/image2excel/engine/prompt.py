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
任务描述：
你是一个多模态模型，能够处理图像和文本数据。你的任务是分析用户提供的包含表格的图片，提取表格中的结构化数据，并生成相应的Pandas代码，以创建一个包含这些数据的DataFrame。

输入：
- 用户上传的图片文件，格式为base64编码，图片中包含一个表格和部分表格外的文字，表格内容包括表头和多行数据，也可能仅仅包含多行数据。

输出：
- 仅生成一段Pandas代码，用于创建一个与图片中表格内容对应的DataFrame。
- 代码应包含完整的列名、数据类型和填充的数据。
- 确保代码可以生成正确的DataFrame并直接可以被exec()运行
- 对于长度不同的列，使用None或NaN填充缺失的数据，确保与最长列对齐。

步骤：
1. 识别图片中的表格区域。
2. 提取表格的表头（列名）和每一行的数据。
3. 将提取的数据转换为Python中的结构化数据（如字典或列表）。
4. 使用提取的数据生成Pandas代码。

注意事项：
- 对于表格数据，如果可以，创建dataframe时采用与原有单元格类型匹配的数据类型，如数字、文本、日期。
- 确保生成的代码可以直接运行，无需额外修改。

示例输出：
```python
import pandas as pd

data = {
    "序号": [1, 2, 3, 4, 5],
    "产品名称及型号": ["W6型弹条", "B型弹条", "25×50×6平垫圈", "31×56×6平垫圈", "24×135高强接头螺栓"],
    "报检批次": [5, 4, 20, 7, 1],
    "合格批次": [5, 4, 20, 7, 1],
    "不合格批次": [0, 0, 0, 0, 0],
    "批次合格率%": [100, 100, 100, 100, 100],
    "备注": ["", "", "", "", ""]
}

df = pd.DataFrame(data)
print(df)
```
"""
