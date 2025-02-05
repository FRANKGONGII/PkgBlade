package org.example.antlr;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;

import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.tree.ParseTree;
import org.antlr.v4.runtime.tree.Trees;

public class Main {
    public static void main(String[] args) throws Exception {
        // 创建 Lexer 和 Parser
        String code = """
            #include "tool_setup.h"

            #include "tool_bname.h"
            
            #include "memdebug.h" /* keep this as LAST include */
            
            #ifndef HAVE_BASENAME
            
            char *tool_basename(char *path)
            {
              char *s1;
              char *s2;
            
              s1 = strrchr(path, '/');
              s2 = strrchr(path, '\\');
            
              if(s1 && s2) {
                path = (s1 > s2) ? s1 + 1 : s2 + 1;
              }
              else if(s1)
                path = s1 + 1;
              else if(s2)
                path = s2 + 1;
            
              return path;
            }
            """;

        // // 检查是否提供了文件路径
        // if (args.length < 1) {
        //     System.err.println("Usage: java Main <file-path>");
        //     System.exit(1);
        // }

        // // 从文件中读取代码内容
        // String filePath = args[0];
        // String code = new String(Files.readAllBytes(Paths.get(filePath)));

        CPP14Lexer lexer = new CPP14Lexer(CharStreams.fromString(code));
        CommonTokenStream tokens = new CommonTokenStream(lexer);
        CPP14Parser parser = new CPP14Parser(tokens);

        // 获取语法树
        CPP14Parser.TranslationUnitContext tree = parser.translationUnit();
        // 打印语法树用于检查
        // System.out.println(printSyntaxTree(parser, tree));

        // 创建自定义 Visitor
        MyCPP14ParserVisitor visitor = new MyCPP14ParserVisitor();

        // 使用 Visitor 遍历语法树
        visitor.visit(tree);

    }

    public static String printSyntaxTree(Parser parser, ParseTree root) {
        StringBuilder buf = new StringBuilder();
        recursive(root, buf, 0, Arrays.asList(parser.getRuleNames()));
        return buf.toString();
    }
    
    private static void recursive(ParseTree aRoot, StringBuilder buf, int offset, List<String> ruleNames) {
        for (int i = 0; i < offset; i++) {
            buf.append("  ");
        }
        buf.append(Trees.getNodeText(aRoot, ruleNames)).append("\n");
        if (aRoot instanceof ParserRuleContext) {
            ParserRuleContext prc = (ParserRuleContext) aRoot;
            if (prc.children != null) {
                for (ParseTree child : prc.children) {
                    recursive(child, buf, offset + 1, ruleNames);
                }
            }
        }
    }
}

