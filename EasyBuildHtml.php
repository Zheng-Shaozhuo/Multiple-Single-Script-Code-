<?php
    if (isset($_REQUEST) && count($_REQUEST) > 0) {
        if ($_REQUEST['mfilename'] && !empty($_REQUEST['flag'])) {
            $filename = $_REQUEST['mfilename'];
            $params = explode(DIRECTORY_SEPARATOR, $filename);
            $filename = end($params);

            $dir = dirname($_SERVER['SCRIPT_FILENAME']);
            $content = null;
            if (file_exists("'./$filename'")) {
                $content = file_get_contents("'./$filename'");
            } else {
                $content = "当前文件打开异常, 请检查.";
            }
            echo "'./$filename'";
            $result = array();
            $targetContent = $content;
            if ("当前文件打开异常, 请检查." != $content) {
                preg_match_all('/<body>([\s\S]*?)<\/body>/U', $content, $result);
//            ob_clean();

                if (count($result) > 0) {
                    $targetContent = $result[1][0];
                }
            }

            echo $targetContent;
        } else {
            $filename = $_REQUEST['filename'];
            $content = $_REQUEST['content'];

            $data = <<<EOF
<!DOCTYPE html>
<html lang="zh-CN">
    <head>
        <meta charset="utf-8">
    </head>
    <body>
        TargetContent
    </body>
</html>
EOF;
            $data = str_replace('TargetContent', $content, $data);
            file_put_contents(iconv('UTF-8', 'GBK', $filename) . '.html', $data);
            $url = trim($_SERVER['HTTP_REFERER'], '#');
        }
    }
?>
<!DOCTYPE html>
<html lang="zh-CN">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- 上述3个meta标签*必须*放在最前面，任何其他内容都*必须*跟随其后！ -->
        <title>Chm文件 分页内容制作</title>

        <!-- Bootstrap -->
        <link href="https://cdn.bootcss.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet">
        <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
        <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
        <!--[if lt IE 9]>
        <script src="https://cdn.bootcss.com/html5shiv/3.7.3/html5shiv.min.js"></script>
        <script src="https://cdn.bootcss.com/respond.js/1.4.2/respond.min.js"></script>
        <![endif]-->
    </head>
    <body>
        <div class="container">
            <div class="row">
                <div class="col-md-12">
                    <form class="form-horizontal" method="post" action="#">
                        <div class="form-group">
                            <h3>简易HTML页面生成</h3>
                            <div class="col-sm-6">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="filename" class="col-sm-2 control-label">修改文件</label>
                            <div class="col-sm-10">
                                <input type="file" class="" id="mfilename" name="mfilename" placeholder="文件标题" style="display: inline-block;">
                                <button type="button" id="modifybtn" class="btn btn-xs btn-danger">提交</button>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="filename" class="col-sm-2 control-label">文件标题</label>
                            <div class="col-sm-10">
                                <input type="text" class="form-control" required id="filename" name="filename" placeholder="文件标题">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="wangEditorBox" class="col-sm-2 control-label">Password</label>
                            <div class="col-sm-10">
                                <div id="wangEditorBox"></div>
                            </div>
                        </div>
                        <div class="form-group">
                            <div class="col-sm-offset-2 col-sm-10">
                                <input type="hidden" id="content" name="content" />
                                <button type="submit" class="btn btn-info">生成页面</button>
                            </div>
                        </div>
                    </form>
                </div>  
            </div>
        </div>

        <script src="https://cdn.bootcss.com/jquery/1.12.4/jquery.min.js"></script>
        <script src="https://cdn.bootcss.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
        <script src="https://cdn.bootcss.com/wangEditor/3.0.16/wangEditor.min.js"></script>

        <script type="text/javascript">
            $(function() {
                var E = window.wangEditor;
                var editor = new E('#wangEditorBox');
                editor.customConfig.uploadImgShowBase64 = true;   // 使用 base64 保存图片
                var text = $('#content');
                editor.customConfig.onchange = function (html) {
                    text.val(html);
                };
                editor.create();
                text.val(editor.txt.html());

                $('#modifybtn').click(function() {
                    if ($('#mfilename').val() == '') {
                        return ;
                    }
                    $.ajax({
                        url: '#',
                        type: 'post',
                        data: {
                            mfilename: $('#mfilename').val(),
                            flag: true
                        },
//                        dataType: 'text',
                        success: function(data) {
                            console.log(data.substr(0, data.indexOf('<!DOCTYPE html>')));
                            editor.txt.html(data.substr(0, data.indexOf('<!DOCTYPE html>')));
                        },
                        error: function(data) {
                            console.log('error');
                        }
                    });
                });
            });
        </script>

        <script type="text/javascript">
            window.onload = function (){
                <?php if(isset($url)) {?>
                init('<?php echo $url;?>');
                <?php } ?>
                function init(url) {
                    alert('文件生成成功，位于当前脚本同级目录下');
                    window.location.href = url;
                }
            };
        </script>
    </body>
</html>