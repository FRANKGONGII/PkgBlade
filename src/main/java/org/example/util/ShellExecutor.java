package org.example.util;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

public class ShellExecutor {
    public static void callShellByExec(String scriptPath) {
        List<String> commands = new ArrayList<>();
        commands.add(scriptPath);

        try {
            // 创建ProcessBuilder对象
            ProcessBuilder processBuilder = new ProcessBuilder(commands);
            // 设置工作目录（可选）
            processBuilder.directory(new File("/path/to/working/directory"));
            // 启动进程
            Process process = processBuilder.start();

            // 获取脚本的输出流
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line); // 打印脚本的输出
            }

            // 等待脚本执行完成
            int exitVal = process.waitFor();
            System.out.println("Exited with error code : " + exitVal);
        } catch (IOException | InterruptedException e) {
            e.printStackTrace();
        }
    }
}