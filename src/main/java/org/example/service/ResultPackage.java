package org.example.service;

import org.example.domain.BladePackage;

public interface ResultPackage {

    // 获取一个包的增改信息
    public void getResizeInfo(BladePackage bladePackage);

    // 获得一个包的基本信息
    public void getBasicInfo(BladePackage bladePackage);
}
