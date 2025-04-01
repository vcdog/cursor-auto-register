// 菜单项切换功能
$(document).ready(function() {
    // 初始化页面导航
    initNavigation();
    
    // 菜单项点击事件
    $('.nav-link').click(function(e) {
        e.preventDefault();
        
        // 获取目标页面
        const targetPage = $(this).data('page');
        
        // 导航到该页面
        navigateToPage(targetPage);
    });
    
    // 响应式处理 - 移动设备上点击菜单后自动收起
    if ($(window).width() <= 768) {
        $('.nav-link').click(function() {
            $('body').removeClass('sidebar-open');
        });
    }
    
    // 添加移动设备菜单切换按钮
    $('<button id="sidebar-toggle" class="btn btn-sm btn-primary position-fixed" style="top: 10px; left: 10px; z-index: 1040;"><i class="fas fa-bars"></i></button>')
        .appendTo('body')
        .click(function() {
            $('body').toggleClass('sidebar-open');
        });
});

// 初始化导航函数
function initNavigation() {
    // 检查URL中是否有哈希值
    let targetPage = window.location.hash.substring(1); // 移除#符号
    
    // 如果哈希值为空或无效，默认显示账号管理页面
    if (!targetPage || !$('#' + targetPage).length) {
        targetPage = 'tasks-accounts';
    }
    
    // 导航到目标页面
    navigateToPage(targetPage);
}

// 导航到指定页面
function navigateToPage(pageId) {
    // 切换活动菜单
    $('.nav-link').removeClass('active');
    $(`.nav-link[data-page="${pageId}"]`).addClass('active');
    
    // 切换显示页面
    $('.page-content').removeClass('active');
    $('#' + pageId).addClass('active');
    
    // 更新URL哈希值，但不触发页面滚动
    if (history.pushState) {
        history.pushState(null, null, '#' + pageId);
    } else {
        window.location.hash = pageId;
    }
}

// 窗口大小变化时的响应式处理
$(window).resize(function() {
    if ($(window).width() > 576) {
        $('body').removeClass('sidebar-open');
    }
}); 

$("#email-type").change(function() {
    if ($(this).val() === "tempemail") {
        $("#tempemail-fields").show();
        $("#zmail-fields").hide();
        $("#gmail-fields").hide();
    } else if ($(this).val() === "zmail") {
        $("#tempemail-fields").hide();
        $("#zmail-fields").show();
        $("#gmail-fields").hide();
    } else if ($(this).val() === "gmail") {
        $("#tempemail-fields").hide();
        $("#zmail-fields").hide();
        $("#gmail-fields").show();
    }
});