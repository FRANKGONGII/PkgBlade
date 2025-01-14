package org.example.service;

public interface GetPackage {

    // 获取下载包路径包的信息
    public void getPackageInfo(String packagePath);

    // 获取包的依赖
    public void getPackageDependency(String packagePath);
}
