package org.example.service;

import org.example.domain.BladePackage;

public interface PrunePackage {

    // 根据一个包标记某些文件
    public void PruneMarkPackage(BladePackage bladePrunePackage, final BladePackage bladePackage);

    // 真正裁剪包
    public void RealPrunePackage(BladePackage bladePackage);
}
