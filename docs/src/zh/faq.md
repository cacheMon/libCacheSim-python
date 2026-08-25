# 常见问题

1.  pip install 失败时如何解决？

    请参阅[安装指南](getting_started/installation.md)。

2.  构建时出现类似 "cannot find Python package" 的错误提示。

    原因是构建 Python 绑定需要 Python 的开发头文件和库文件。

    如果你拥有管理员权限，可以使用系统的包管理器安装所需的软件包。例如：

    *   **Debian/Ubuntu**：`sudo apt install python3-dev`
    *   **RHEL/CentOS/Fedora**：`sudo yum install python3-devel`
    *   **macOS**：通常用 Homebrew 安装 Python（`brew install python`）即可。

    另外，如果你把 Python 安装在了自定义位置，则需要设置环境变量来帮助构建系统找到它。请记得将下面命令中的占位符替换为你的实际路径。

    ```shell
    export CMAKE_ARGS="-DPython3_ROOT_DIR=${Python3_ROOT_DIR} -DPython3_INCLUDE_DIR=${Python3_INCLUDE_DIR} -DPython3_EXECUTABLE=${Python3_EXECUTABLE}"
    ```
