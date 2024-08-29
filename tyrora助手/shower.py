import os
import re
import shutil

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox


class Stats:
    def __init__(self):
        self.ui = QUiLoader().load('./ui/界面.ui')
        self.ui.pushButton_12.clicked.connect(self.去图片夹冗余文件)
        self.ui.pushButton_11.clicked.connect(self.去图片冗余文件)
        self.ui.pushButton_19.clicked.connect(self.检查文件夹内md文件的图片完整性)
        self.ui.pushButton_21.clicked.connect(self.检查文md文件的图片完整性)
        self.ui.pushButton_20.clicked.connect(self.md和assets和md内图片全部换名字)

    def 返回文件夹内的md文件(self, 文件夹路径):
        if not 文件夹路径:
            return False, None
        所有md文件 = [f for f in os.listdir(文件夹路径) if f.endswith('.md')]
        if not 所有md文件:
            return False, None
        return True, 所有md文件
    def 去图片夹冗余文件(self):
        '''
        默认只会处理.assets中的冗余图片
        :return:
        '''
        文件夹路径 = self.获取文件夹路径()
        文件夹是否存在md文件, 所有md文件 = self.返回文件夹内的md文件(文件夹路径)
        if not 文件夹是否存在md文件:
            self.显示消息("去冗余文件失败", "选择的文件夹中没有Markdown文件！")
            return
        总冗余图片数 = 0
        总失败图片数 = 0
        详细信息 = []
        for md文件 in 所有md文件:
            md文件路径 = os.path.join(文件夹路径, md文件)
            冗余图片数, 失败图片数, 删除的图片 = self.处理单个md文件(md文件路径)
            总冗余图片数 += 冗余图片数
            总失败图片数 += 失败图片数
            if 冗余图片数 > 0 or 失败图片数 > 0:
                文件信息 = [
                    f"文件 '{md文件}':",
                    f"  - 删除了 {冗余图片数} 个冗余图片"
                ]
                if 失败图片数 > 0:
                    文件信息.append(f"  - {失败图片数} 个图片删除失败")
                if 删除的图片:
                    文件信息.append("  - 删除的图片:")
                    文件信息.extend([f"    * {图片}" for 图片 in 删除的图片])
                详细信息.extend(文件信息)
                详细信息.append("")  # 添加空行分隔不同文件的信息
        总结信息 = f"处理了 {len(所有md文件)} 个Markdown文件\n" \
                   f"共删除 {总冗余图片数} 个冗余图片\n" \
                   f"有 {总失败图片数} 个图片删除失败\n\n" \
                   f"详细信息:\n" + "\n".join(详细信息)
        self.显示消息("去冗余文件完成", 总结信息)
    def 处理单个md文件(self, md文件路径):
        '''
        默认只会处理.assets中的冗余图片
        :param md文件路径:
        :return:
        '''
        文件内容 = self.读取文件内容(md文件路径)
        所有图片路径 = self.返回md内所有图片路劲(文件内容)
        文件名 = os.path.splitext(os.path.basename(md文件路径))[0]
        图片文件夹 = os.path.join(os.path.dirname(md文件路径), f'{文件名}.assets')
        if not os.path.exists(图片文件夹):return 0, 0, []  # 如果.assets文件夹不存在，直接返回
        冗余图片路径 = self.找到冗余的图片路劲(图片文件夹, 所有图片路径)
        if not 冗余图片路径:return 0, 0, []  # 如果没有冗余图片，直接返回
        成功, 消息 = self.删除冗余图片(图片文件夹, 冗余图片路径)
        if 成功:return len(冗余图片路径), 0, 冗余图片路径
        else:
            失败数 = 消息.count('\n')  # 假设每个失败的图片占一行
            return len(冗余图片路径) - 失败数, 失败数, 冗余图片路径[:len(冗余图片路径) - 失败数]
    def 去图片冗余文件(self):
        '''
        默认只会处理.assets中的冗余图片
        :return:
        '''
        在md文件内是否找到图, 文件路劲, 所有图片路劲 = self.判断md文件内是否存在文件()
        if 在md文件内是否找到图 == False:return
        文件名 = os.path.splitext(os.path.basename(文件路劲))[0]
        图片文件夹 = os.path.join(os.path.dirname(文件路劲), f'{文件名}.assets')
        if not os.path.exists(图片文件夹):
            self.显示消息("去冗余文件失败", f"文件夹 {图片文件夹} 不存在！")
            return
        冗余图片路劲 = self.找到冗余的图片路劲(图片文件夹, 所有图片路劲)
        if not 冗余图片路劲:
            self.显示消息("去冗余文件", "没有发现冗余图片。")
            return
        成功, 消息 = self.删除冗余图片(图片文件夹, 冗余图片路劲)
        if 成功:
            self.显示消息("去冗余文件成功", f"删除的图片个数：{len(冗余图片路劲)}")
        else:
            self.显示消息("去冗余文件失败", f"删除图片失败！原因：{消息}")
    def 找到冗余的图片路劲(self, 图片文件夹, 所有图片路劲):
        文件夹内所有文件 = os.listdir(图片文件夹)
        使用中的图片名字加后缀 = [os.path.basename(路径) for 路径 in 所有图片路劲]
        冗余图片 = [文件 for 文件 in 文件夹内所有文件 if 文件 not in 使用中的图片名字加后缀]
        return 冗余图片
    def 删除冗余图片(self, 图片文件夹, 冗余图片路劲):
        成功删除的图片个数 = 0
        失败的图片 = []
        for 图片 in 冗余图片路劲:
            try:
                os.remove(os.path.join(图片文件夹, 图片))
                成功删除的图片个数 += 1
            except Exception as e:
                失败的图片.append(f"{图片}: {str(e)}")
        if 失败的图片:
            return False, f"成功删除 {成功删除的图片个数} 个图片，但有 {len(失败的图片)} 个图片删除失败。\n失败的图片：\n" + "\n".join(
                失败的图片)
        else:
            return True, f"成功删除所有 {成功删除的图片个数} 个冗余图片。"
    def 判断md文件内是否存在文件(self):
        文件路劲 = self.获取文件路径()
        if not 文件路劲:
            return False, None, None
        文件内容 = self.读取文件内容(文件路劲)
        所有图片路劲 = self.返回md内所有图片路劲(文件内容)
        if not 所有图片路劲:
            self.显示消息("去冗余文件失败", "没有找到任何图片！")
            return False, None, None
        return True, 文件路劲, 所有图片路劲
    def 读取文件内容(self, 路径):
        with open(路径, 'r', encoding='utf-8') as 文件:
            return 文件.read()
    def 显示消息(self, 标题, 内容):
        QMessageBox.information(self.ui, 标题, 内容)
    def 获取文件路径(self):
        return QFileDialog.getOpenFileName()[0]
    def 获取文件夹路径(self):
        文件夹路径 = QFileDialog.getExistingDirectory(self.ui, "选择文件夹")
        return 文件夹路径
    def 返回md内所有图片路劲(self, 文件内容):
        图片正则 = r'!\[.*?\]\((.*?)\)|<img.*?src=[\'\"](.*?)[\'\"].*?>'
        所有匹配 = re.findall(图片正则, 文件内容)
        所有路径 = [路径 for 匹配 in 所有匹配 for 路径 in 匹配 if 路径]
        所有路径 = list(set(所有路径))  # 去重
        return 所有路径
    def 检查文件夹内md文件的图片完整性(self):
        文件夹路径 = self.获取文件夹路径()
        _, 所有md文件 = self.返回文件夹内的md文件(文件夹路径)
        if not 所有md文件:
            self.显示消息("检查失败", "选择的文件夹中没有Markdown文件！")
            return
        结果 = []
        for md文件 in 所有md文件:
            md文件路径 = os.path.join(文件夹路径, md文件)
            缺失图片 = self.检查单个md文件图片完整性(md文件路径)
            if 缺失图片:
                结果.append(f"文件 '{md文件}' 缺失以下图片:\n" + "\n".join(f"  - {图片}" for 图片 in 缺失图片))
        if 结果:self.显示消息("检查完成", "\n\n".join(结果))
        else:self.显示消息("检查完成", "所有Markdown文件的图片都完整！")
    def 检查文md文件的图片完整性(self):
        md文件路径 = self.获取文件路径()
        if not md文件路径:return
        缺失图片 = self.检查单个md文件图片完整性(md文件路径)
        if 缺失图片:self.显示消息("检查完成", f"文件缺失以下图片:\n" + "\n".join(f"  - {图片}" for 图片 in 缺失图片))
        else:self.显示消息("检查完成", "文件的所有图片都完整！")

    def 检查单个md文件图片完整性(self, md文件路径):
        文件内容 = self.读取文件内容(md文件路径)
        所有图片路径 = self.返回md内所有图片路劲(文件内容)
        文件名 = os.path.splitext(os.path.basename(md文件路径))[0]
        图片文件夹 = os.path.join(os.path.dirname(md文件路径), f'{文件名}.assets')
        缺失图片 = []
        for 图片路径 in 所有图片路径:
            图片文件名 = os.path.basename(图片路径)
            完整图片路径 = os.path.join(图片文件夹, 图片文件名)
            if not os.path.exists(完整图片路径):缺失图片.append(图片路径)
        return 缺失图片
    def md和assets和md内图片全部换名字(self):
        md文件路径 = self.获取文件路径()
        if not md文件路径:return
        新文件名 = QFileDialog.getSaveFileName(self.ui, "保存新文件", "", "Markdown Files (*.md)")[0]
        if not 新文件名:return
        # 读取文件内容
        文件内容 = self.读取文件内容(md文件路径)
        所有图片路径 = self.返回md内所有图片路劲(文件内容)
        旧文件名 = os.path.splitext(os.path.basename(md文件路径))[0]
        新文件名_无后缀 = os.path.splitext(os.path.basename(新文件名))[0]
        # 更新文件内容中的图片路径
        for 旧图片路径 in 所有图片路径:
            新图片路径 = 旧图片路径.replace(f'{旧文件名}.assets', f'{新文件名_无后缀}.assets')
            文件内容 = 文件内容.replace(旧图片路径, 新图片路径)
        # 写入新文件
        with open(新文件名, 'w', encoding='utf-8') as f:
            f.write(文件内容)
        # 重命名并移动assets文件夹
        旧assets路径 = os.path.join(os.path.dirname(md文件路径), f'{旧文件名}.assets')
        新assets路径 = os.path.join(os.path.dirname(新文件名), f'{新文件名_无后缀}.assets')
        if os.path.exists(旧assets路径):
            shutil.move(旧assets路径, 新assets路径)
        self.显示消息("重命名完成", f"文件已重命名并保存为 {新文件名}\nAssets文件夹已更新")

if __name__ == '__main__':
    app = QApplication([])
    stats = Stats()
    stats.ui.show()
    app.exec_()
