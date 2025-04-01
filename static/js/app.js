// 全局变量
const REFRESH_INTERVAL = 30000; // 30秒
let currentPage = 1;
let totalPages = 1;
let itemsPerPage = 10;
let currentSortField = 'created_at';
let currentSortOrder = 'desc';

// 页面加载完成后执行
$(document).ready(function() {
    // 初始化应用
    initializeApplication();
});

// 应用初始化函数 - 提高代码组织性
function initializeApplication() {
    // 绑定分页事件必须在DOM准备好后立即执行
    bindPaginationEvents();
    
    // 绑定排序事件
    bindSortEvents();
    
    // 确保不使用ID排序
    if (currentSortField === 'id') {
        currentSortField = 'created_at';
    }
    
    // 加载配置
    loadConfig();
    
    // 初始加载数据
    loadAccounts(1, itemsPerPage);

    // 设置定时刷新
    setupTaskRefresh();
    
    // 绑定所有事件处理函数
    bindEventHandlers();
}

// 事件处理绑定函数 - 将所有事件绑定集中在一起
function bindEventHandlers() {
    // 按钮事件监听
    $("#refresh-btn").click(function() {
        showLoading();
        loadAccounts(1, itemsPerPage, $("#search-input").val());
    });
    
    $("#start-registration").click(function() {
        startTaskManually();
    });
    
    $("#stop-registration").click(function() {
        stopTaskManually();
    });
    
    $("#search-btn").click(function() {
        filterAccounts();
    });
    
    $("#search-input").keypress(function(e) {
        if (e.which === 13) {
            filterAccounts();
        }
    });
    
    // 可以添加更多事件绑定...

    // 在bindEventHandlers函数中添加配置相关事件
    $("#edit-config-btn").click(function(e) {
        e.preventDefault(); // 明确阻止任何默认行为
        console.log("点击编辑配置按钮");
        enableConfigForm(true);
    });

    $("#cancel-config-btn").click(function(e) {
        e.preventDefault();
        console.log("取消编辑配置");
        enableConfigForm(false);
        loadConfig(); // 重新加载原始配置
    });

    $("#config-form").submit(function(e) {
        console.log("click config-form submit");
        e.preventDefault();
        saveConfig();
    });

    // 代理设置切换事件
    $("#use-proxy").change(function() {
        toggleProxySettings();
    });

    // 重启服务按钮事件
    $("#restart-service-btn").click(function() {
        showConfirmDialog(
            '重启服务', 
            '确定要重启服务吗？重启过程可能需要几秒钟，期间服务将不可用。',
            function() {
                restartService();
            }
        );
    });

    // 重置机器ID按钮事件
    $("#reset-machine-btn").click(function() {
        showConfirmDialog(
            '重置机器ID', 
            '确定要重置机器ID吗？这将解除当前设备的绑定限制，但可能需要重新登录所有账号。',
            function() {
                resetMachineId();
            }
        );
    });

    // 导出账号按钮点击事件
    $("#export-accounts-btn").click(function() {
        exportAccounts();
    });
    
    // 导入账号按钮点击事件
    $("#import-accounts-btn").click(function() {
        $("#import-file-input").click();
    });
    
    // 导入文件选择事件
    $("#import-file-input").change(function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            
            // 读取文件预览内容
            const reader = new FileReader();
            reader.onload = function(event) {
                try {
                    const data = JSON.parse(event.target.result);
                    
                    if (Array.isArray(data)) {
                        // 显示导入确认对话框
                        $("#import-count").text(data.length);
                        const importModal = new bootstrap.Modal(document.getElementById('import-confirm-modal'));
                        importModal.show();
                        
                        // 存储文件引用，用于后续导入
                        window.fileToImport = file;
                    } else {
                        showAlert('danger', '无效的数据格式：必须是账号对象的数组');
                    }
                } catch (err) {
                    showAlert('danger', '解析JSON文件失败：' + err.message);
                }
                
                // 重置文件输入，允许再次选择同一文件
                $("#import-file-input").val('');
            };
            
            reader.readAsText(file);
        }
    });
    
    // 确认导入按钮点击事件
    $("#confirm-import-btn").click(function() {
        if (window.fileToImport) {
            importAccounts(window.fileToImport);
            bootstrap.Modal.getInstance(document.getElementById('import-confirm-modal')).hide();
        }
    });
}

// 全局变量
let accounts = [];
let filteredAccounts = [];
let refreshTimer;

// 显示加载遮罩
function showLoading(message = '加载中，请稍候...') {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.add('show');
    $("#loading-overlay p").text(message);
}

// 隐藏加载遮罩
function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.classList.remove('show');
}

// 加载账号数据
function loadAccounts(page = 1, perPage = itemsPerPage, search = '', sortField = currentSortField, sortOrder = currentSortOrder) {
    showLoading();
    
    // 构建URL查询参数
    let params = new URLSearchParams({
        page: page,
        per_page: perPage,
        sort_by: sortField,
        order: sortOrder
    });
    
    if (search) {
        params.append('search', search);
    }
    
    const url = `/accounts?${params.toString()}`;
    
    $.ajax({
        url: url,
        method: 'GET',
        success: function(response) {
            if (response.success) {
                accounts = response.data;
                
                // 更新分页和排序信息
                currentPage = response.pagination.page;
                totalPages = response.pagination.total_pages;
                itemsPerPage = response.pagination.per_page;
                currentSortField = response.sort.field;
                currentSortOrder = response.sort.order;
                
                // 新增：更新账号统计信息
                const totalAccounts = response.pagination.total_count || 0;
                const maxAccounts = parseInt($("#max-accounts").text()) || 10;
                const remainingSlots = Math.max(0, maxAccounts - totalAccounts);
                
                $("#current-count").text(totalAccounts);
                $("#remaining-slots").text(`剩余: ${remainingSlots}`);
                
                // 计算使用百分比
                const usagePercent = maxAccounts > 0 ? Math.round((totalAccounts / maxAccounts) * 100) : 0;
                
                // 更新进度条
                $(".battery-progress").attr("data-percent", usagePercent);
                $(".battery-percent").text(`${usagePercent}%`);
                
                // 更新排序控件
                $("#sort-field").val(currentSortField);
                $("#sort-order").val(currentSortOrder);
                
                // 添加淡入效果
                $("#accounts-table").css("opacity", 0);
                
                // 更新UI
                updateAccountsTable(accounts);
                updatePagination(currentPage, totalPages);
                $("#total-accounts").text(response.pagination.total_count);
                
                // 更新每页记录数下拉框
                $("#per-page").val(itemsPerPage);
                
                // 淡入表格
                $("#accounts-table").animate({opacity: 1}, 300);
                
                hideLoading();
            } else {
                showAlert('danger', '加载账号失败: ' + response.message);
                hideLoading();
            }
        },
        error: function(xhr) {
            hideLoading();
            showAlert('danger', '加载账号失败: ' + (xhr.responseJSON?.detail || xhr.statusText));
        }
    });
}

// 更新分页控件
function updatePagination(currentPage, totalPages) {
    // 清除现有页码
    $(".pagination .page-number").remove();
    
    // 决定显示哪些页码
    let pages = [];
    
    // 限制显示的页码数量，使UI更加紧凑
    if (totalPages <= 5) {
        // 总页数少于5，显示所有页码
        for (let i = 1; i <= totalPages; i++) {
            pages.push(i);
        }
    } else {
        // 总页数大于5，使用更紧凑的布局
        
        // 总是显示第一页
        pages.push(1);
        
        // 当前页在前3页
        if (currentPage <= 3) {
            pages.push(2, 3, 4, '...', totalPages);
        }
        // 当前页在后3页
        else if (currentPage >= totalPages - 2) {
            pages.push('...', totalPages-3, totalPages-2, totalPages-1, totalPages);
        }
        // 当前页在中间
        else {
            pages.push('...', currentPage-1, currentPage, currentPage+1, '...', totalPages);
        }
    }
    
    // 创建页码元素 - 简化HTML生成
    let pageElements = '';
    
    pages.forEach(page => {
        if (page === '...') {
            pageElements += `<li class="page-item disabled page-number"><a class="page-link" href="#">…</a></li>`;
        } else {
            const isActive = page === currentPage ? 'active' : '';
            pageElements += `<li class="page-item page-number ${isActive}"><a class="page-link" href="#" data-page="${page}">${page}</a></li>`;
        }
    });
    
    // 使用insertBefore而不是after，确保顺序正确
    $(pageElements).insertBefore("#next-page");
    
    // 更新上一页/下一页按钮状态
    $("#prev-page").toggleClass('disabled', currentPage === 1);
    $("#next-page").toggleClass('disabled', currentPage === totalPages);
    
    // 更新分页信息文本
    $("#current-page").text(currentPage);
    $("#total-pages").text(totalPages);
}

// 修复分页事件绑定 - 确保在DOM加载完成后绑定
function bindPaginationEvents() {
    // 上一页按钮 - 使用事件委托
    $(document).on('click', "#prev-page:not(.disabled) a", function(e) {
        e.preventDefault();
        if (currentPage > 1) {
            loadAccounts(currentPage - 1, itemsPerPage, $("#search-input").val());
        }
    });
    
    // 下一页按钮 - 使用事件委托
    $(document).on('click', "#next-page:not(.disabled) a", function(e) {
        e.preventDefault();
        if (currentPage < totalPages) {
            loadAccounts(currentPage + 1, itemsPerPage, $("#search-input").val());
        }
    });
    
    // 页码点击 - 使用事件委托确保动态生成的元素也能响应
    $(document).on('click', '.page-number:not(.disabled) .page-link', function(e) {
        e.preventDefault();
        const page = parseInt($(this).attr('data-page'));
        if (!isNaN(page)) {
            loadAccounts(page, itemsPerPage, $("#search-input").val());
        }
    });
    
    // 每页显示记录数变更
    $(document).on('change', "#per-page", function() {
        itemsPerPage = parseInt($(this).val());
        loadAccounts(1, itemsPerPage, $("#search-input").val());
    });
}

// 修改搜索函数
function filterAccounts() {
    const searchTerm = $("#search-input").val().trim();
    loadAccounts(1, itemsPerPage, searchTerm);
}

// 更新账号表格
function updateAccountsTable(accounts) {
    const accountsBody = $('#accounts-tbody');
    accountsBody.empty();
    
    if (accounts.length === 0) {
        // 添加空状态提示
        accountsBody.html(`
            <tr>
                <td colspan="7" class="text-center py-4">
                    <div class="py-5">
                        <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                        <p class="text-muted">暂无账号数据</p>
                    </div>
                </td>
            </tr>
        `);
        return;
    }
    
    // 渲染每行数据
    accounts.forEach((account, index) => {
        // 完整的行模板，包含所有单元格内容
        const row = `
            <tr id="account-row-${account.id}" data-status="${account.status}" 
                class="${account.status === 'deleted' ? 'table-danger' : account.status === 'disabled' ? 'table-warning' : ''}">
                <td class="email-column">
                    ${account.email}
                    <span class="badge ${account.status === 'active' ? 'bg-success' : account.status === 'disabled' ? 'bg-warning' : 'bg-danger'} ms-2">
                        ${account.status === 'active' ? '正常' : account.status === 'disabled' ? '停用' : '删除'}
                    </span>
                </td>
                <td class="d-none d-lg-table-cell password-cell">
                    <span class="password-text">${maskPassword(account.password)}</span>
                    <i class="fas fa-eye toggle-password" data-password="${account.password}" title="显示/隐藏密码"></i>
                    <i class="fas fa-copy copy-btn ms-1" data-copy="${account.password}" title="复制密码"></i>
                </td>
                ${renderTokenColumn(account.token, account.id, account.email)}
                ${renderUsageProgress(account.usage_limit)}
                <td class="d-none d-lg-table-cell">
                    ${account.created_at || '未知'}
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary get-usage-btn" data-email="${account.email}" title="查询使用量">
                            <i class="fas fa-chart-pie"></i>
                        </button>
                    </div>
                </td>
                <td class="operation-column">
                    <div class="d-flex flex-wrap gap-1">
                        ${account.status !== 'active' ? 
                            `<button class="btn btn-sm btn-outline-success status-action" data-email="${account.email}" data-id="${account.id}" data-status="active" title="设为正常">
                                <i class="fas fa-check-circle"></i>
                            </button>` : ''}
                            
                        ${account.status !== 'disabled' ? 
                            `<button class="btn btn-sm btn-outline-warning status-action" data-email="${account.email}" data-id="${account.id}" data-status="disabled" title="停用账号">
                                <i class="fas fa-pause-circle"></i>
                            </button>` : ''}
                            
                        ${account.status !== 'deleted' ? 
                            `<button class="btn btn-sm btn-outline-danger status-action" data-email="${account.email}" data-id="${account.id}" data-status="deleted" title="标记删除">
                                <i class="fas fa-times-circle"></i>
                            </button>` : ''}
                            
                        <button class="btn btn-sm btn-danger delete-account-btn" data-email="${account.email}" data-id="${account.id}" title="永久删除">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        accountsBody.append(row);
    });
    
    // 绑定事件
    bindTableEvents();
    
    // 更新表头排序指示
    $('.sortable').removeClass('asc desc');
    $(`.sortable[data-field="${currentSortField}"]`).addClass(currentSortOrder);
}

// 渲染账号表格
function renderAccountsTable() {
    const accountsBody = $('#accounts-tbody');
    accountsBody.empty();
    
    if (filteredAccounts.length === 0) {
        // 添加空状态提示
        accountsBody.html(`
            <tr>
                <td colspan="7" class="text-center py-4">
                    <div class="py-5">
                        <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                        <p class="text-muted">暂无账号数据</p>
                    </div>
                </td>
            </tr>
        `);
        return;
    }
    
    // 计算当前页的数据
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredAccounts.length);
    const currentPageData = filteredAccounts.slice(startIndex, endIndex);
    
    console.log(`当前页数据: ${currentPageData.length}条 (第${currentPage}页)`);
    
    // 渲染每行数据
    currentPageData.forEach((account, index) => {
        // 完整的行模板，包含所有单元格内容
        const row = `
            <tr id="account-row-${account.id}" data-status="${account.status}" 
                class="${account.status === 'deleted' ? 'table-danger' : account.status === 'disabled' ? 'table-warning' : ''}">
                <td class="d-none d-md-table-cell">${startIndex + index + 1}</td>
                <td class="email-column">
                    ${account.email}
                    <span class="badge ${account.status === 'active' ? 'bg-success' : account.status === 'disabled' ? 'bg-warning' : 'bg-danger'} ms-2">
                        ${account.status === 'active' ? '正常' : account.status === 'disabled' ? '停用' : '删除'}
                    </span>
                </td>
                <td class="d-none d-lg-table-cell password-cell">
                    <span class="password-text">${maskPassword(account.password)}</span>
                    <i class="fas fa-eye toggle-password" data-password="${account.password}" title="显示/隐藏密码"></i>
                    <i class="fas fa-copy copy-btn ms-1" data-copy="${account.password}" title="复制密码"></i>
                </td>
                ${renderTokenColumn(account.token, account.id)}
                ${renderUsageProgress(account.usage_limit)}
                <td class="d-none d-lg-table-cell">
                    ${account.created_at || '未知'}
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary get-usage-btn" data-email="${account.email}" title="查询使用量">
                            <i class="fas fa-chart-pie"></i>
                        </button>
                    </div>
                </td>
                <td class="operation-column">
                    <div class="d-flex flex-wrap gap-1">
                        ${account.status !== 'active' ? 
                            `<button class="btn btn-sm btn-outline-success status-action" data-email="${account.email}" data-id="${account.id}" data-status="active" title="设为正常">
                                <i class="fas fa-check-circle"></i>
                            </button>` : ''}
                            
                        ${account.status !== 'disabled' ? 
                            `<button class="btn btn-sm btn-outline-warning status-action" data-email="${account.email}" data-id="${account.id}" data-status="disabled" title="停用账号">
                                <i class="fas fa-pause-circle"></i>
                            </button>` : ''}
                            
                        ${account.status !== 'deleted' ? 
                            `<button class="btn btn-sm btn-outline-danger status-action" data-email="${account.email}" data-id="${account.id}" data-status="deleted" title="标记删除">
                                <i class="fas fa-times-circle"></i>
                            </button>` : ''}
                            
                        <button class="btn btn-sm btn-danger delete-account-btn" data-email="${account.email}" data-id="${account.id}" title="永久删除">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        accountsBody.append(row);
    });
    
    // 绑定事件
    bindTableEvents();
    renderPagination();
}

// 渲染分页
function renderPagination() {
    const totalPages = Math.ceil(filteredAccounts.length / itemsPerPage);
    const pagination = $("#pagination");
    pagination.empty();
    
    if (totalPages <= 1) {
        return;
    }
    
    const paginationNav = $('<nav aria-label="Page navigation"></nav>');
    const paginationUl = $('<ul class="pagination"></ul>');
    
    // 上一页按钮
    paginationUl.append(`
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" aria-label="Previous" ${currentPage !== 1 ? 'onclick="changePage(' + (currentPage - 1) + '); return false;"' : ''}>
                <span aria-hidden="true">&laquo;</span>
            </a>
        </li>
    `);
    
    // 页码按钮
    for (let i = 1; i <= totalPages; i++) {
        paginationUl.append(`
            <li class="page-item ${currentPage === i ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
            </li>·
        `);
    }
    
    // 下一页按钮
    paginationUl.append(`
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" aria-label="Next" ${currentPage !== totalPages ? 'onclick="changePage(' + (currentPage + 1) + '); return false;"' : ''}>
                <span aria-hidden="true">&raquo;</span>
            </a>
        </li>
    `);
    
    paginationNav.append(paginationUl);
    pagination.append(paginationNav);
}

// 更改页码
function changePage(page) {
    currentPage = page;
    renderAccountsTable();
}

// 获取账号用量详情并更新数据库
function getAccountUsage(email) {
    showLoading();
    fetch(`/account/${encodeURIComponent(email)}/usage`)
        .then(res => res.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                // 创建并显示用量信息模态框
                const modal = $(`
                    <div class="modal fade" tabindex="-1">
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">账号用量信息</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="mb-3">
                                        <strong>邮箱:</strong> ${data.email}
                                    </div>
                                    <div class="mb-3">
                                        <strong>剩余额度:</strong> ${data.usage.remaining_balance !== null ? data.usage.remaining_balance : '未知'}
                                    </div>
                                    <div class="mb-3">
                                        <strong>剩余天数:</strong> ${data.usage.remaining_days !== null ? data.usage.remaining_days : '未知'}
                                    </div>
                                    <div class="mb-3">
                                        <strong>状态:</strong> 
                                        <span class="badge ${data.usage.status === 'active' ? 'bg-success' : 'bg-danger'}">
                                            ${data.usage.status === 'active' ? '活跃' : '不活跃'}
                                        </span>
                                    </div>
                                    <div class="mt-3 text-muted small">
                                        <strong>更新时间:</strong> ${formatDateTime(data.timestamp)}
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `);
                
                $('body').append(modal);
                const modalInstance = new bootstrap.Modal(modal[0]);
                modalInstance.show();
                
                // 模态框关闭时移除DOM
                modal[0].addEventListener('hidden.bs.modal', function() {
                    modal.remove();
                });
            }
        })
        .catch(error => {
            console.error('获取账号用量失败:', error);
            showAlert('获取账号用量失败', 'danger');
            hideLoading();
        });
}

// 更新账号用量到数据库
function updateAccountUsageLimit(email, usageLimit) {
    fetch(`/account/${encodeURIComponent(email)}/update-usage`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ usage_limit: usageLimit })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            console.log(`账号 ${email} 用量数据已更新到数据库`);
        } else {
            console.error(`更新账号 ${email} 用量数据失败:`, data.message);
        }
    })
    .catch(error => {
        console.error(`更新账号 ${email} 用量数据时发生错误:`, error);
    });
}

// 修复任务状态更新问题
function startTaskManually() {
    showLoading();
    fetch('/registration/start', {
        method: 'GET'
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showAlert('定时任务已成功启动', 'success');
            checkTaskStatus();
        } else {
            showAlert(`启动任务失败: ${data.message || '未知错误'}`, 'danger');
        }
    })
    .catch(error => {
        console.error('启动任务时发生错误:', error);
        hideLoading();
        showAlert('启动任务失败，请稍后重试', 'danger');
    });
}

// 同样添加到停止任务函数
function stopTaskManually() {
    showLoading();
    fetch('/registration/stop', {
        method: 'GET'
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showAlert('定时任务已成功停止', 'success');
            
            // 立即更新任务状态 - 添加这段代码
            fetch('/registration/status')
                .then(res => res.json())
                .then(statusData => {
                    updateTaskStatusUI(statusData);
                });
        } else {
            showAlert(`停止任务失败: ${data.message || '未知错误'}`, 'danger');
        }
    })
    .catch(error => {
        console.error('停止任务时发生错误:', error);
        hideLoading();
        showAlert('停止任务失败，请稍后重试', 'danger');
    });
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('复制成功，Token已复制到剪贴板', 'success');
    }).catch(err => {
        console.error('复制失败:', err);
        showAlert('复制失败', 'danger');
    });
}

// 显示通知
function showAlert(message, type, isSpecial = false) {
    const alertId = 'alert-' + Date.now();
    const alertClass = isSpecial ? 
        `alert-${type} special-alert animate__animated animate__bounceIn` : 
        `alert-${type} animate__animated animate__fadeInRight`;
    
    const alert = $(`
        <div id="${alertId}" class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${isSpecial ? '<i class="fas fa-star me-2"></i>' : ''}${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);
    
    $("#alert-container").append(alert);
    
    // 5秒后自动消失
    setTimeout(() => {
        $(`#${alertId}`).alert('close');
    }, 5000);
}

// 日期时间格式化
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '-';
    
    try {
        const date = new Date(dateTimeString);
        if (isNaN(date.getTime())) return dateTimeString;
        
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const seconds = date.getSeconds().toString().padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    } catch (error) {
        return dateTimeString;
    }
}

// 修改掩码函数，增加对用户名的特殊处理
function maskText(text, showChars = 6, isUsername = false) {
    if (!text) return '';
    
    // 用户名特殊处理 - 只显示前1/3
    if (isUsername) {
        const showLength = Math.ceil(text.length / 3);
        if (text.length <= showLength) return text;
        return `${text.substring(0, showLength)}...`;
    }
    
    // 其他文本使用标准处理
    if (text.length <= showChars) return text;
    return `${text.substring(0, showChars)}...`;
}

// 隐藏密码
function maskPassword(password) {
    if (!password) return '';
    return '•'.repeat(password.length);
}

// 页面加载动画
document.addEventListener('DOMContentLoaded', function() {
    // 修改动画类添加代码，删除对已删除元素的引用
    const elements = [
        {selector: '.card', animation: 'animate__fadeIn', delay: 0.2}
    ];
    
    elements.forEach(item => {
        const elems = document.querySelectorAll(item.selector);
        elems.forEach((el, index) => {
            el.classList.add('animate__animated', item.animation);
            
            if (item.delay) {
                const delay = item.stagger ? item.delay * (index + 1) : item.delay;
                el.style.animationDelay = `${delay}s`;
            }
        });
    });
});

// 烟花动画实现
const Fireworks = {
    canvas: null,
    ctx: null,
    particles: [],
    
    init: function() {
        this.canvas = document.getElementById('fireworks-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    },
    
    resizeCanvas: function() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    },
    
    start: function() {
        this.canvas.style.display = 'block';
        this.particles = [];
        
        // 创建5次烟花，间隔300ms
        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                const x = Math.random() * this.canvas.width;
                const y = Math.random() * this.canvas.height * 0.6;
                this.createParticles(x, y);
            }, i * 300);
        }
        
        this.animate();
        
        // 5秒后停止动画
        setTimeout(() => {
            this.canvas.style.display = 'none';
        }, 5000);
    },
    
    createParticles: function(x, y) {
        const colors = ['#ff595e', '#ffca3a', '#8ac926', '#1982c4', '#6a4c93'];
        
        for (let i = 0; i < 80; i++) {
            const particle = {
                x: x,
                y: y,
                size: Math.random() * 4 + 1,
                color: colors[Math.floor(Math.random() * colors.length)],
                velocity: {
                    x: (Math.random() - 0.5) * 8,
                    y: (Math.random() - 0.5) * 8
                },
                alpha: 1,
                decay: Math.random() * 0.02 + 0.01
            };
            
            this.particles.push(particle);
        }
    },
    
    animate: function() {
        if (this.particles.length === 0) return;
        
        requestAnimationFrame(() => this.animate());
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];
            
            // 添加重力
            p.velocity.y += 0.05;
            
            // 更新位置
            p.x += p.velocity.x;
            p.y += p.velocity.y;
            
            // 减少透明度
            p.alpha -= p.decay;
            
            // 绘制粒子
            this.ctx.save();
            this.ctx.globalAlpha = p.alpha;
            this.ctx.fillStyle = p.color;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();
            
            // 移除消失的粒子
            if (p.alpha <= 0) {
                this.particles.splice(i, 1);
                i--;
            }
        }
    }
};

// 初始化烟花
Fireworks.init();

// 绑定表格交互事件
function bindTableEvents() {
    // 显示/隐藏用户名
    $('.toggle-username').off('click').on('click', function() {
        const username = $(this).data('username');
        const usernameText = $(this).prev('.username-text');
        
        if (usernameText.text() === username) {
            usernameText.text(maskText(username, 6, true));
        } else {
            usernameText.text(username);
        }
    });
    
    // 显示/隐藏密码
    $('.toggle-password').off('click').on('click', function() {
        const password = $(this).data('password');
        const passwordText = $(this).prev('.password-text');
        
        if (passwordText.text() === password) {
            passwordText.text(maskPassword(password));
        } else {
            passwordText.text(password);
        }
    });
    
    // 显示/隐藏Token
    $('.toggle-token').off('click').on('click', function() {
        const token = $(this).data('token');
        const tokenText = $(this).prev('.token-text');
        
        if (tokenText.text() === token) {
            tokenText.text(maskText(token));
        } else {
            tokenText.text(token);
        }
    });
    
    // 复制按钮
    $('.copy-btn').off('click').on('click', function() {
        const textToCopy = $('#tokenFullText').val();
        copyToClipboard(textToCopy);
    });
    
    // 获取用量按钮
    $('.get-usage-btn').off('click').on('click', function() {
        const email = $(this).data('email');
        getAccountUsage(email);
    });
    
    // 查看使用记录按钮
    $('.view-records-btn').off('click').on('click', function() {
        const email = $(this).data('email');
        const id = $(this).data('id');
        getAccountUsageRecords(email, id);
    });

    // 删除按钮
    $('.delete-account-btn').off('click').on('click', function() {
        const email = $(this).data('email');
        const id = $(this).data('id');
        $('#deleteEmailConfirm').text(email);
        $('#deleteIdConfirm').text(id || '无');
        
        // 重置并重新绑定确认删除按钮事件
        $('#confirmDeleteBtn').off('click').on('click', function() {
            deleteAccount(email, id, true);
        });
        
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        deleteModal.show();
    });

    // 状态操作按钮
    $('.status-action').off('click').on('click', function(e) {
        e.preventDefault();
        const email = $(this).data('email');
        const id = $(this).data('id');
        const status = $(this).data('status');
        updateAccountStatus(email, id, status);
    });

    // 查看Token按钮
    $('.view-token-btn').off('click').on('click', function() {
        const token = $(this).data('token');
        const accountId = $(this).data('account-id');
        $('#tokenFullText').val(token);
        $('#useTokenBtn').data('account-id', accountId);
        new bootstrap.Modal(document.getElementById('tokenViewModal')).show();
    });
    
    // 使用Token按钮
    $('#useTokenBtn').off('click').on('click', function() {
        const accountId = $(this).data('account-id');
        if (!accountId) {
            showAlert('账号ID无效', 'danger');
            return;
        }
        
        showLoading();
        fetch(`/account/use-token/${accountId}`, {
            method: 'POST'
        })
        .then(res => res.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showAlert(data.message, 'success');
                $('#tokenViewModal').modal('hide');
            } else {
                showAlert(`使用Token失败: ${data.message || '未知错误'}`, 'danger');
            }
        })
        .catch(error => {
            console.error('使用Token时发生错误:', error);
            hideLoading();
            showAlert('使用Token失败，请稍后重试', 'danger');
        });
    });
}

// 更新删除确认按钮事件处理
$('#confirmDeleteBtn').click(function() {
    const email = $(this).data('email');
    const id = $(this).data('id');
    deleteAccount(email, id, true);
});

// 修改updateAccountStatus函数，确保正确发送请求体
function updateAccountStatus(email, id, status) {
    showLoading();
    // 优先使用ID API，如果ID存在的话
    const apiUrl = id ? 
        `/account/id/${id}/status` : 
        `/account/${encodeURIComponent(email)}/status`;
    
    fetch(apiUrl, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: status })  // 确保这里的字段名是status
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            let statusText = '';
            if (status === 'active') statusText = '正常';
            else if (status === 'disabled') statusText = '停用';
            else if (status === 'deleted') statusText = '删除';
            
            showAlert(`账号${id ? '(ID:'+id+')' : ''} ${email} 已成功设置为${statusText}状态`, 'success');
            loadAccounts(1, itemsPerPage);
        } else {
            showAlert(`更新账号状态失败: ${data.message || '未知错误'}`, 'danger');
        }
    })
    .catch(error => {
        console.error('更新账号状态时发生错误:', error);
        hideLoading();
        showAlert('更新账号状态失败，请稍后重试', 'danger');
    });
}

// 修改deleteAccount函数，支持通过ID删除
function deleteAccount(email, id, hardDelete = true) {
    showLoading();
    // 优先使用ID API，如果ID存在的话
    const apiUrl = id ? 
        `/account/id/${id}${hardDelete ? '?hard_delete=true' : ''}` : 
        `/account/${encodeURIComponent(email)}${hardDelete ? '?hard_delete=true' : ''}`;
    
    fetch(apiUrl, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showAlert(`账号${id ? '(ID:'+id+')' : ''} ${email} 已成功删除`, 'success');
            // 关闭模态框
            $('#deleteConfirmModal').modal('hide');
            // 重新加载账号列表
            loadAccounts(1, itemsPerPage);
        } else {
            showAlert(`删除账号失败: ${data.message || '未知错误'}`, 'danger');
        }
    })
    .catch(error => {
        console.error('删除账号时发生错误:', error);
        hideLoading();
        showAlert('删除账号失败，请稍后重试', 'danger');
    });
}


// 完全重构额度显示函数，精确匹配参考代码
function renderUsageProgress(usageLimit) {
    // 计算使用进度
    const premiumUsed =  150 - usageLimit;
    const premiumTotal = 150;
    const premiumRemaining = premiumTotal - premiumUsed;
    const premiumPercent = Math.round((premiumUsed / premiumTotal) * 100);
    
    return `
        <td class="usage-info">
            <div class="usage-numbers">
                <span class="used-count">${premiumUsed}</span>
                <span class="separator">/</span>
                <span class="total-count">${premiumTotal}</span>
                <span class="remaining-count">(剩余: ${premiumRemaining})</span>
            </div>
            <div class="battery-progress" data-percent="${Math.round(premiumPercent / 10) * 10}">
                <div class="battery-bars">
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                    <span class="battery-bar"></span>
                </div>
                <span class="battery-percent">${premiumPercent}%</span>
            </div>
        </td>
    `;
}

// 修改Token列的渲染方式
function renderTokenColumn(token, accountId, email) {
    return `
        <td class="token-column">
            <button class="btn btn-sm btn-outline-info view-token-btn" data-token="${token}" data-account-id="${accountId}">
                <i class="fas fa-eye"></i> 查看Token
            </button>
            <button class="btn btn-sm btn-outline-info view-records-btn" data-email="${email}" data-id="${accountId}" title="查看使用记录">
                <i class="fas fa-history"></i>
            </button>
        </td>
    `;
}

// 加载配置函数
function loadConfig() {
    showLoading();
    $.ajax({
        url: '/config',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                const config = response.data;
                
                // 现有字段设置...
                
                // 设置代理配置
                $("#use-proxy").prop("checked", config.USE_PROXY === "True");
                $("#proxy-type").val(config.PROXY_TYPE || "http");
                $("#proxy-host").val(config.PROXY_HOST || "");
                $("#proxy-port").val(config.PROXY_PORT || "");
                $("#proxy-timeout").val(config.PROXY_TIMEOUT || "10");
                $("#proxy-username").val(config.PROXY_USERNAME || "");
                $("#proxy-password").val(config.PROXY_PASSWORD || "");
                
                // 触发动态UA的change事件
                $("#dynamic-useragent").trigger('change');
                // 根据是否启用代理来显示/隐藏代理设置
                toggleProxySettings();
                
                $("#browser-useragent").val(config.BROWSER_USER_AGENT);
                $("#accounts-limit").val(config.MAX_ACCOUNTS);
                $("#captcha-method").val(config.EMAIL_CODE_TYPE || "API");
                $("#email-domains").val(config.EMAIL_DOMAINS);
                $("#email-username").val(config.EMAIL_USERNAME);
                $("#email-pin").val(config.EMAIL_PIN);
                $("#browser-path").val(config.BROWSER_PATH || '');
                $("#cursor-path").val(config.CURSOR_PATH || '');

                if (config.EMAIL_DOMAIN) {
                    // 获取第一个域名作为示例
                    const firstDomain = config.EMAIL_DOMAIN;
                    // 更新输入框提示
                    $('#email-username').attr('placeholder', `仅输入用户名部分，例如：ddcat28（完整地址将是 ddcat28@${firstDomain}）`);
                    // 添加域名显示标签
                    if (!$('#email-domain-suffix').length) {
                        $('#email-username').after(`<span id="email-domain-suffix" class="input-group-text bg-light">@${firstDomain}</span>`);
                        // 将输入框和域名标签包装在input-group中
                        $('#email-username, #email-domain-suffix').wrapAll('<div class="input-group"></div>');
                    } else {
                        $('#email-domain-suffix').text(`@${firstDomain}`);
                    }
                }
                
                $("#email-type").val(config.EMAIL_TYPE);
                $("#email-proxy-enabled").prop('checked', config.EMAIL_PROXY_ENABLED || false);
                if (config.EMAIL_PROXY_ENABLED) {
                    $("#email-proxy-address").val(config.EMAIL_PROXY_ADDRESS);
                    $("#email-api").val(config.EMAIL_API);
                }
                if (config.EMAIL_TYPE == "tempemail") {
                    $("#tempemail-fields").show();
                    $("#zmail-fields").hide();
                } else if (config.EMAIL_TYPE == "zmail") {
                    $("#tempemail-fields").hide();
                    $("#zmail-fields").show();
                }
                
                hideLoading();

            } else {
                showAlert('danger', '加载配置失败: ' + response.message);
                hideLoading();
            }
        },
        error: function(xhr) {
            hideLoading();
            showAlert('danger', '加载配置失败: ' + xhr.statusText);
        }
    });
}

// 添加代理设置的显示/隐藏控制
function toggleProxySettings() {
    if ($("#use-proxy").is(":checked")) {
        $("#proxy-settings").show();
    } else {
        $("#proxy-settings").hide();
    }
}

// 添加配置保存回调，支持重启
function saveConfig() {
    showLoading();
    const isDynamicUA = $(this).prop('checked');
    const configData = {
        BROWSER_HEADLESS: $("#browser-headless").val() === 'true',
        DYNAMIC_USERAGENT: isDynamicUA,
        BROWSER_USER_AGENT: isDynamicUA ? "" : $("#browser-useragent").val(),
        MAX_ACCOUNTS: parseInt($("#accounts-limit").val()),
        EMAIL_CODE_TYPE: $("#captcha-method").val(),
        EMAIL_DOMAINS: $("#email-domains").val(),
        EMAIL_USERNAME: $("#email-username").val(),
        EMAIL_PIN: $("#email-pin").val(),
        BROWSER_PATH: $("#browser-path").val(),
        CURSOR_PATH: $("#cursor-path").val(),
        // 代理设置（确保这些字段存在）
        USE_PROXY: $("#use-proxy").is(":checked"),
        PROXY_TYPE: $("#proxy-type").val(),
        PROXY_HOST: $("#proxy-host").val(),
        PROXY_PORT: $("#proxy-port").val(),
        PROXY_TIMEOUT: parseInt($("#proxy-timeout").val()) || 10,
        PROXY_USERNAME: $("#proxy-username").val(),
        PROXY_PASSWORD: $("#proxy-password").val()
    };
    
    $.ajax({
        url: '/config',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(configData),
        success: function(response) {
            hideLoading();
            if (response.success) {
                // 添加重启询问提示
                showConfirmDialog(
                    '配置已成功保存', 
                    '需要重启服务才能使更改生效。是否立即重启服务？',
                    function() {
                        // 确认重启
                        restartService();
                    }
                );
                enableConfigForm(false);
            } else {
                showAlert('danger', '保存配置失败: ' + response.message);
            }
        },
        error: function(xhr) {
            hideLoading();
            showAlert('danger', '保存配置失败: ' + xhr.statusText);
        }
    });
}

// 添加确认对话框函数
function showConfirmDialog(title, message, confirmCallback) {
    // 如果已存在对话框，先移除
    if ($("#confirm-dialog").length) {
        $("#confirm-dialog").remove();
    }
    
    const dialogHTML = `
        <div class="modal fade" id="confirm-dialog" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">${message}</div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-primary" id="confirm-yes">确认</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(dialogHTML);
    
    const modal = new bootstrap.Modal(document.getElementById('confirm-dialog'));
    modal.show();
    
    $("#confirm-yes").click(function() {
        modal.hide();
        if (typeof confirmCallback === 'function') {
            confirmCallback();
        }
    });
}

// 更新重启服务函数
function restartService() {
    showLoading('服务正在重新配置，请稍候...');
    
    $.ajax({
        url: '/restart',
        method: 'POST',
        success: function(response) {
            if (response.success) {
                // 显示成功消息
                hideLoading();
                showAlert('success', response.message || '服务配置已更新，正在刷新页面...');
                
                // 延迟3秒后刷新页面
                setTimeout(function() {
                    window.location.reload();
                }, 3000);
            } else {
                hideLoading();
                showAlert('danger', '重启服务失败: ' + (response.message || '未知错误'));
            }
        },
        error: function(xhr) {
            hideLoading();
            showAlert('danger', '重启服务请求失败，请手动刷新页面');
            
            // 延迟5秒后尝试刷新页面
            setTimeout(function() {
                window.location.reload();
            }, 5000);
        }
    });
}

// 启用/禁用配置表单
function enableConfigForm(enable) {
    const inputs = $('#config-form select, #config-form input');
    if (enable) {
        inputs.prop('disabled', false);
        // 如果动态UA已启用，保持UA输入框禁用
        if ($("#dynamic-useragent").prop('checked')) {
            $("#browser-useragent").prop('disabled', true);
        }
        // 显示按钮容器而不是单个按钮
        $('#config-actions').show();
        $('#edit-config-btn').hide();
    } else {
        inputs.prop('disabled', true);
        // 隐藏按钮容器
        $('#config-actions').hide();
        $('#edit-config-btn').show();
    }
}

// 动态User-Agent切换逻辑
$("#dynamic-useragent").change(function() {
    const isDynamicUA = $(this).prop('checked');
    if (isDynamicUA) {
        $("#browser-useragent").prop('disabled', true);
        $("#useragent-input-container").addClass('text-muted');
    } else {
        // 只有在编辑模式下才启用输入框
        const isEditMode = !$("#edit-config-btn").is(":visible");
        $("#browser-useragent").prop('disabled', !isEditMode);
        $("#useragent-input-container").removeClass('text-muted');
    }
});

// 修改任务状态显示函数，保留状态处理逻辑
function updateTaskStatusDisplay(statusData) {
    // 获取UI元素引用
    const statusBadge = $("#registration-status");
    const taskStatusText = $("#task-status-text");
    const taskIcon = $("#task-status i");
    
    // 直接使用服务器返回的统计数据
    const stats = statusData;
    
    // 计算实际使用的账号数量
    const usedCount = stats.active_count || 0;
    const maxAccounts = stats.max_accounts || 10; 
    const remainingSlots = Math.max(0, maxAccounts - usedCount);
    // 更新显示
    $("#current-count").text(usedCount);
    $("#max-accounts").text(maxAccounts);
    $("#remaining-slots").text(`剩余: ${remainingSlots}`);
    // 计算使用百分比
    const usagePercent = maxAccounts > 0 ? Math.round((usedCount / maxAccounts) * 100) : 0;
    
    // 更新进度条
    $(".battery-progress").attr("data-percent", usagePercent);
    $(".battery-percent").text(`${usagePercent}%`);

    // 更新任务详情
    if (statusData.registration_details) {
        const details = statusData.registration_details;
        // 更新统计信息
        if (details.statistics) {
            $("#total-runs").text(details.statistics.total_runs);
            $("#successful-runs").text(details.statistics.successful_runs);
            $("#failed-runs").text(details.statistics.failed_runs);
            $("#success-rate").text(details.statistics.success_rate);
        }
    }
    
    // 根据任务状态更新UI
    switch(statusData.task_status) {
        case "running":
            statusBadge.removeClass("bg-success bg-warning bg-danger").addClass("bg-primary");
            statusBadge.text("运行中");
            taskStatusText.text(statusData.status_message || "任务正在运行中");
            taskIcon.removeClass("fa-check-circle fa-pause-circle fa-times-circle").addClass("fa-spinner fa-spin");
            taskIcon.removeClass("text-success text-warning text-danger").addClass("text-primary");
            
            // 显示/隐藏按钮
            $("#start-registration").hide();
            $("#stop-registration").show();
            $("#registration-details").show();
            break;
            
        case "stopped":
        default:
            statusBadge.removeClass("bg-primary bg-warning bg-danger").addClass("bg-success");
            statusBadge.text("空闲中");
            taskStatusText.text(statusData.status_message || "系统空闲中，可以开始新任务");
            taskIcon.removeClass("fa-spinner fa-spin fa-pause-circle fa-times-circle").addClass("fa-check-circle");
            taskIcon.removeClass("text-primary text-warning text-danger").addClass("text-success");
            
            // 显示/隐藏按钮
            $("#start-registration").show();
            $("#stop-registration").hide();
            $("#registration-details").hide();
            break;
    }
    
}

// 绑定排序事件
function bindSortEvents() {
    // 字段排序变化
    $("#sort-field").change(function() {
        currentSortField = $(this).val();
        loadAccounts(1, itemsPerPage, $("#search-input").val(), currentSortField, currentSortOrder);
    });
    
    // 排序方向变化
    $("#sort-order").change(function() {
        currentSortOrder = $(this).val();
        loadAccounts(1, itemsPerPage, $("#search-input").val(), currentSortField, currentSortOrder);
    });
}

// 修改表头排序配置，移除ID相关设置
function addTableHeaderSorting() {
    // 可排序的列 - 移除ID相关配置
    const sortableColumns = {
        'th-email': 'email',
        'th-date': 'created_at',
        'th-usage': 'usage_limit'
    };
    
    // 为表头添加排序类和点击事件
    Object.keys(sortableColumns).forEach(thId => {
        const $th = $(`#${thId}`);
        $th.addClass('sortable');
        
        // 设置初始排序指示
        if (sortableColumns[thId] === currentSortField) {
            $th.addClass(currentSortOrder);
        }
        
        $th.click(function() {
            const field = sortableColumns[thId];
            
            // 如果点击当前排序列，切换排序方向
            if (field === currentSortField) {
                currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                // 否则，切换排序列并设置默认为降序
                currentSortField = field;
                currentSortOrder = 'desc';
            }
            
            // 更新排序控件
            $("#sort-field").val(currentSortField);
            $("#sort-order").val(currentSortOrder);
            
            // 重新加载数据
            loadAccounts(1, itemsPerPage, $("#search-input").val(), currentSortField, currentSortOrder);
        });
    });
}

// 设置定时任务刷新
function setupTaskRefresh() {
    // 清除可能存在的旧定时器
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    // 设置新的定时刷新
    refreshTimer = setInterval(function() {
        // 检查任务状态
        checkTaskStatus();
        
        // 如果在账号管理页面，刷新账号列表
        if ($("#tasks-accounts").hasClass('active')) {
            loadAccounts(currentPage, itemsPerPage, $("#search-input").val(), currentSortField, currentSortOrder);
        }
    }, REFRESH_INTERVAL);
    
    // 初始加载任务状态
    checkTaskStatus();

    // 添加注册进度刷新
    setInterval(function() {
        // 仅在任务运行时更新进度
        if ($("#registration-status").hasClass("bg-primary")) {
            updateRegistrationProgress();
        }
    }, 2000); // 每2秒更新一次进度
}

// 检查任务状态
function checkTaskStatus() {
    fetch('/registration/status')
        .then(response => response.json())
        .then(data => {
            // 确保有账号统计数据
            updateTaskStatusDisplay(data);

            // 更新任务运行时间和下次运行时间
            let registration_details = data.registration_details;
            if (registration_details.last_run) {
                $("#last-run").text(formatDateTime(data.registration_details.last_run));
            }
            
            if (data.registration_details.next_run) {
                const nextRunTime = new Date(registration_details.next_run * 1000);
                const now = new Date();
                const timeLeft = Math.max(0, Math.floor((nextRunTime - now) / 1000));
                
                if (timeLeft > 0) {
                    $("#next-run").text(`${formatDateTime(registration_details.next_run * 1000)} (还有${formatTimeLeft(timeLeft)})`);
                } else {
                    $("#next-run").text(`${formatDateTime(registration_details.next_run * 1000)}`);
                }
            } else {
                $("#next-run").text("未排程");
            }
            
            // 更新注册进度和消息
            if (registration_details.registration_progress) {
                $("#registration-progress").text(registration_details.registration_progress);
            }
            
            if (registration_details.registration_message) {
                $("#registration-message").text(registration_details.registration_message);
            }
        })
        .catch(error => {
            console.error('获取任务状态出错:', error);
        });
}

// 格式化日期时间
function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });
}

// 格式化剩余时间
function formatTimeLeft(seconds) {
    if (seconds < 60) {
        return `${seconds}秒`;
    } else if (seconds < 3600) {
        return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}小时${minutes}分`;
    }
}

// 添加重置机器ID函数
function resetMachineId() {
    showLoading();
    
    $.ajax({
        url: '/reset-machine',
        method: 'GET',
        success: function(response) {
            hideLoading();
            if (response.success) {
                showAlert('success', '成功重置机器ID。' + (response.message || ''));
                
                // 询问是否需要重启服务以应用更改
                setTimeout(function() {
                    showConfirmDialog(
                        '重启服务', 
                        '机器ID已重置，建议重启服务以确保更改生效。是否立即重启？',
                        function() {
                            restartService();
                        }
                    );
                }, 1000);
            } else {
                showAlert('danger', '重置机器ID失败: ' + (response.message || '未知错误'));
            }
        },
        error: function(xhr) {
            hideLoading();
            showAlert('danger', '重置机器ID失败: ' + (xhr.responseJSON?.message || xhr.statusText || '未知错误'));
        }
    });
}

// 导出账号函数
function exportAccounts() {
    showLoading();
    
    // 直接使用浏览器下载功能
    const downloadLink = document.createElement('a');
    downloadLink.href = '/accounts/export';
    downloadLink.download = 'cursor_accounts.json';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    
    setTimeout(() => {
        hideLoading();
        showAlert('success', '账号导出请求已发送，文件将自动下载');
    }, 1000);
}

// 导入账号函数
function importAccounts(file) {
    showLoading();
    
    const formData = new FormData();
    formData.append('file', file);
    
    // 发送导入请求
    $.ajax({
        url: '/accounts/import',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            hideLoading();
            if (response.success) {
                showAlert('success', response.message);
                
                // 刷新账号列表
                loadAccounts(1, itemsPerPage);
            } else {
                showAlert('danger', '导入账号失败: ' + response.message);
            }
        },
        error: function(xhr) {
            hideLoading();
            showAlert('danger', '导入账号失败: ' + (xhr.responseJSON?.detail || xhr.statusText));
        }
    });
}

// 获取账号使用记录
function getAccountUsageRecords(email, id) {
    showLoading();
    
    // 设置模态框中的账号邮箱
    $('#recordEmail').text(email);
    
    // 清空记录列表
    $('#usageRecordBody').empty();
    
    fetch(`/account/${id}/usage-records`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                const records = data.records;
                
                if (records && records.length > 0) {
                    // 隐藏无记录提示
                    $('#no-records').hide();
                    
                    // 显示记录
                    records.forEach(record => {
                        const row = `
                            <tr>
                                <td>${formatDateTime(record.created_at)}</td>
                                <td>${record.ip || '-'}</td>
                                <td class="small text-truncate" style="max-width: 300px;" title="${record.user_agent || ''}">
                                    ${record.user_agent || '-'}
                                </td>
                            </tr>
                        `;
                        $('#usageRecordBody').append(row);
                    });
                } else {
                    // 显示无记录提示
                    $('#usageRecordBody').empty();
                    $('#no-records').show();
                }
                
                // 显示模态框
                new bootstrap.Modal(document.getElementById('usageRecordModal')).show();
            } else {
                showAlert(`获取使用记录失败: ${data.message || '未知错误'}`, 'danger');
            }
        })
        .catch(error => {
            console.error('获取使用记录时发生错误:', error);
            hideLoading();
            showAlert('获取使用记录失败，请稍后重试', 'danger');
        });
}

// 修改注册进度更新函数
function updateRegistrationProgress() {
    $.ajax({
        url: "/registration/progress",
        method: "GET",
        success: function(data) {
            // 更新进度值
            const percentage = data.percentage;
            
            // 更新进度条
            $("#registration-progress-bar").css("width", percentage + "%");
            $("#registration-progress-bar").attr("aria-valuenow", percentage);
            $("#registration-progress-bar").text(percentage + "%");
            
            // 同时更新文本显示
            $("#registration-progress").text(percentage + "%");
            
            // 更新进度信息
            $("#registration-message").text(data.message);
            
            // 显示注册详情区域
            if (percentage > 0) {
                $("#registration-details").show();
            }
        }
    });
}