package org.example.antlr;


public class MyCPP14ParserVisitor extends CPP14ParserBaseVisitor<Void> {

    // @Override
    // public Void visitDeclarationStatement(CPP14Parser.DeclarationStatementContext ctx) { 
    //     System.out.println("declare");
    //     return visitChildren(ctx); 
    // }


    @Override
    public Void visitPostfixExpression(CPP14Parser.PostfixExpressionContext ctx) {
        System.out.println("Visiting: " + ctx.getText());
        // 判断是否是函数调用规则，检查 LeftParen 是否存在，表示函数调用
        if (ctx.LeftParen() != null) {
            // 获取函数名
            String functionName = ctx.postfixExpression().getText();
            System.out.println("Function call detected: " + functionName);
        }
        return visitChildren(ctx);
    }
}
