"""Write by Cursor"""


import traceback




from itertools import chain
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import os
import sys
import traceback
from datetime import datetime
import queue

from src.defined import ENCODE
import src.util.nodeTrans

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from manager import MyMessages
from src.net.Me import Me
from src.manager.Nodes import Nodes
from src.manager.OthersMessages import OthersMessages
from src.net.Node import Node
from src.model.NodeInfo import NodeInfo
from src.model.Message import RootMessage, ReplyMessage
from util import nodeTrans
from src.manager.MyMessages import MyMessages

class TuneGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Tune - P2P Network Node Manager")
        self.root.geometry("1200x800")
        
        # ノード名の設定
        self.nodeName = tk.StringVar(value="MyNode")
        
        # BANされたノードのリスト（GUI用、実際のBAN状態はNodesクラスで管理）
        self.bannedNodes = set()
        
        # 非同期処理用のキュー
        self.asyncQueue = queue.Queue()
        
        # GUIの初期化
        self.setupGui()
        
        # ノードの状態
        self.isRunning = False
        self.serveThread = None
        self.syncerThread = None
        
        # 定期的な更新
        self.updateInterval = 1000  # 1秒（より頻繁な更新）
        self.scheduleUpdate()
        
        # 非同期処理の開始
        self.processAsyncTasks()
        
        # 選択されたメッセージの情報
        self.selectedMessage = None
        # トラフィックタブ用
        self.trafficData = []
    
    def setupGui(self):
        # メインフレーム
        mainFrame = ttk.Frame(self.root, padding="10")
        mainFrame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        mainFrame.columnconfigure(0, weight=1)
        mainFrame.rowconfigure(1, weight=1)
        
        # 基本設定フレーム
        self.setupBasicSettings(mainFrame)
        
        # タブコントロール
        self.setupTabs(mainFrame)
    
    def setupBasicSettings(self, parent):
        """基本設定（ノード名、最大ノード数、制御ボタン）"""
        basicFrame = ttk.LabelFrame(parent, text="基本設定", padding="10")
        basicFrame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        basicFrame.columnconfigure(1, weight=1)
        
        # ノード名設定
        ttk.Label(basicFrame, text="ノード名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(basicFrame, textvariable=self.nodeName, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 制御ボタン
        controlFrame = ttk.Frame(basicFrame)
        controlFrame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.startButton = ttk.Button(controlFrame, text="ノード開始", command=self.startNode)
        self.startButton.pack(side=tk.LEFT, padx=5)
        
        self.stopButton = ttk.Button(controlFrame, text="ノード停止", command=self.stopNode, state=tk.DISABLED)
        self.stopButton.pack(side=tk.LEFT, padx=5)
    
    def setupTabs(self, parent):
        """タブコントロールの設定"""
        # ノートブック（タブ）を作成
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ノード管理タブ
        self.setupNodeManagementTab()
        
        # メッセージタブ
        self.setupMessageTab()
        
        # トラフィックタブ
        self.setupTrafficTab()  # 追加
        
        # ログタブ
        self.setupLogTab()
    
    def setupNodeManagementTab(self):
        """ノード管理タブの設定"""
        nodeTab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(nodeTab, text="ノード管理")
        nodeTab.columnconfigure(0, weight=1)
        nodeTab.rowconfigure(1, weight=1)
        
        # 初期ノード追加
        addNodeFrame = ttk.LabelFrame(nodeTab, text="初期ノード追加", padding="5")
        addNodeFrame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        addNodeFrame.columnconfigure(1, weight=1)
        
        ttk.Label(addNodeFrame, text="Id:").grid(row=0, column=0, sticky=tk.W)
        self.nodeInput = ttk.Entry(addNodeFrame, width=50)
        self.nodeInput.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Button(addNodeFrame, text="追加", command=self.addInitialNode).grid(row=0, column=2, padx=5)
        
        # ノード情報表示
        infoFrame = ttk.LabelFrame(nodeTab, text="ノード情報", padding="5")
        infoFrame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        infoFrame.columnconfigure(0, weight=1)
        infoFrame.rowconfigure(1, weight=1)
        
        # 自分のノード情報
        self.myInfoText = tk.StringVar(value="ノードが開始されていません")
        ttk.Label(infoFrame, textvariable=self.myInfoText, font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        
        # 接続ノード一覧
        nodesFrame = ttk.Frame(infoFrame)
        nodesFrame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        nodesFrame.columnconfigure(0, weight=1)
        nodesFrame.rowconfigure(0, weight=1)
        
        # ツリービューでノード一覧を表示
        columns = ("Id", "名前", "公開鍵", "状態")
        self.nodesTree = ttk.Treeview(nodesFrame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.nodesTree.heading(col, text=col)
            self.nodesTree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(nodesFrame, orient=tk.VERTICAL, command=self.nodesTree.yview)
        self.nodesTree.configure(yscrollcommand=scrollbar.set)
        
        self.nodesTree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # ノード操作ボタン
        nodeButtonsFrame = ttk.Frame(infoFrame)
        nodeButtonsFrame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(nodeButtonsFrame, text="選択ノードをBAN", command=self.banSelectedNode).pack(side=tk.LEFT, padx=5)
        ttk.Button(nodeButtonsFrame, text="BAN解除", command=self.unbanSelectedNode).pack(side=tk.LEFT, padx=5)
        ttk.Button(nodeButtonsFrame, text="BANリスト表示", command=self.showBanList).pack(side=tk.LEFT, padx=5)
        ttk.Button(nodeButtonsFrame, text="手動更新", command=self.manualUpdate).pack(side=tk.LEFT, padx=5)
    
    def setupMessageTab(self):
        """メッセージタブの設定"""
        messageTab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(messageTab, text="メッセージ")
        messageTab.columnconfigure(0, weight=1)
        messageTab.rowconfigure(1, weight=1)
        
        # メッセージ送信
        messageFrame = ttk.LabelFrame(messageTab, text="メッセージ送信", padding="5")
        messageFrame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        messageFrame.columnconfigure(1, weight=1)
        
        ttk.Label(messageFrame, text="メッセージ:").grid(row=0, column=0, sticky=tk.W)
        self.messageInput = ttk.Entry(messageFrame, width=60)
        self.messageInput.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Button(messageFrame, text="送信", command=self.sendMessage).grid(row=0, column=2, padx=5)
        
        # メッセージ一覧
        messagesFrame = ttk.LabelFrame(messageTab, text="メッセージ一覧", padding="5")
        messagesFrame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        messagesFrame.columnconfigure(0, weight=1)
        messagesFrame.rowconfigure(0, weight=1)
        
        # メッセージリストボックス（スクロール可能）
        self.messagesListbox = tk.Listbox(messagesFrame, height=25, font=("Arial", 10))
        messagesScrollbar = ttk.Scrollbar(messagesFrame, orient=tk.VERTICAL, command=self.messagesListbox.yview)
        self.messagesListbox.configure(yscrollcommand=messagesScrollbar.set)
        
        # メッセージリストの選択イベント
        self.messagesListbox.bind('<<ListboxSelect>>', self.onMessageSelect)
        
        self.messagesListbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        messagesScrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 選択されたメッセージの詳細表示
        detailFrame = ttk.LabelFrame(messageTab, text="メッセージ詳細", padding="5")
        detailFrame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        detailFrame.columnconfigure(0, weight=1)
        
        self.messageDetailText = tk.Text(detailFrame, height=8, width=80, wrap=tk.WORD, state=tk.DISABLED)
        detailScrollbar = ttk.Scrollbar(detailFrame, orient=tk.VERTICAL, command=self.messageDetailText.yview)
        self.messageDetailText.configure(yscrollcommand=detailScrollbar.set)
        
        self.messageDetailText.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        detailScrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 選択されたメッセージの情報
        self.selectedMessage = None
        
        # メッセージデータの管理
        self.messagesData = []  # メッセージとリプライの階層構造
    
    def onMessageSelect(self, event):
        """メッセージが選択された時の処理"""
        selection = self.messagesListbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if 0 <= index < len(self.messagesData):
            self.selectedMessage = self.messagesData[index]
            self.displayMessageDetail()
    
    def displayMessageDetail(self):
        """選択されたメッセージの詳細を表示"""
        if not self.selectedMessage:
            return
        
        # 詳細テキストを有効化
        self.messageDetailText.config(state=tk.NORMAL)
        self.messageDetailText.delete(1.0, tk.END)
        
        # ルートメッセージの詳細
        root_msg = self.selectedMessage['root']
        timestamp = datetime.fromtimestamp(root_msg.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        detail_text = f"【ルートメッセージ】\n"
        detail_text += f"時刻: {timestamp}\n"
        detail_text += f"送信者: {root_msg.author.getNodeInfo().name if root_msg.author else '自分'}\n"
        detail_text += f"内容:\n{root_msg.content}\n\n"
        
        # リプライの詳細
        if self.selectedMessage['replies']:
            detail_text += f"【リプライ ({len(self.selectedMessage['replies'])}件)】\n"
            for i, reply in enumerate(self.selectedMessage['replies'], 1):
                reply_timestamp = datetime.fromtimestamp(reply.timestamp).strftime("%H:%M:%S")
                detail_text += f"\n{i}. {reply_timestamp} - "
                detail_text += f"{reply.fromNode.getNodeInfo().name if reply.fromNode else '不明'}\n"
                detail_text += f"   {reply.content}\n"
        else:
            detail_text += "【リプライなし】\n"
        
        self.messageDetailText.insert(1.0, detail_text)
        self.messageDetailText.config(state=tk.DISABLED)
    
    def setupLogTab(self):
        """ログタブの設定"""
        logTab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(logTab, text="ログ")
        logTab.columnconfigure(0, weight=1)
        logTab.rowconfigure(0, weight=1)
        
        # ログ表示
        logFrame = ttk.LabelFrame(logTab, text="システムログ", padding="5")
        logFrame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        logFrame.columnconfigure(0, weight=1)
        logFrame.rowconfigure(0, weight=1)
        
        self.logText = scrolledtext.ScrolledText(logFrame, height=25, width=100)
        self.logText.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ログ操作ボタン
        logButtonsFrame = ttk.Frame(logTab)
        logButtonsFrame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(logButtonsFrame, text="ログクリア", command=self.clearLog).pack(side=tk.LEFT, padx=5)
        ttk.Button(logButtonsFrame, text="ログ保存", command=self.saveLog).pack(side=tk.LEFT, padx=5)

    def processAsyncTasks(self):
        """非同期タスクを処理"""
        try:
            while not self.asyncQueue.empty():
                task = self.asyncQueue.get_nowait()
                if task:
                    task()
        except queue.Empty:
            pass
        
        # 100ms後に再度チェック
        self.root.after(100, self.processAsyncTasks)

    def runAsync(self, func, *args, **kwargs):
        """非同期で関数を実行"""
        def async_wrapper():
            try:
                result = func(*args, **kwargs)
                # 結果をGUIスレッドで処理
                self.root.after(0, lambda: self.handleAsyncResult(result))
            except Exception as e:
                self.root.after(0, lambda: self.handleAsyncError(e))
        
        threading.Thread(target=async_wrapper, daemon=True).start()

    def handleAsyncResult(self, result):
        """非同期処理の結果を処理"""
        # 必要に応じて結果を処理
        pass

    def handleAsyncError(self, error):
        """非同期処理のエラーを処理"""
        self.logMessage(f"非同期処理エラー: {str(error)}")

    def logMessage(self, message):
        """ログにメッセージを追加"""
        timestamp = time.strftime("%H:%M:%S")
        self.logText.insert(tk.END, f"[{timestamp}] {message}\n")
        self.logText.see(tk.END)
    
    def startNode(self):
        """ノードを開始（非同期）"""
        # ボタンを即座に無効化
        self.startButton.config(state=tk.DISABLED)
        self.logMessage("ノード開始中...")
        
        # 非同期でノード開始処理を実行
        self.runAsync(self._startNodeInternal)
    
    def _startNodeInternal(self):
        """ノード開始の内部処理"""
        try:
            # ノード名を設定
            Me.setName(self.nodeName.get())
            
            # スレッドを開始
            self.serveThread = threading.Thread(target=Me.serve, daemon=True)
            self.syncerThread = threading.Thread(target=Me.syncer, daemon=True)
            
            self.serveThread.start()
            self.syncerThread.start()
            
            self.isRunning = True
            
            # GUIスレッドでボタン状態を更新
            self.root.after(0, self._updateStartButtonState)
            
            self.logMessage(f"ノード '{self.nodeName.get()}' を開始しました")
            self.logMessage(f"ポート: {Me.getPort()}")
            self.logMessage(f"公開鍵: {Me.getPubKey()}")
            self.logMessage("デバッグ用ID（同コンピューター用）: "+nodeTrans.idFromNodeIAndP(f"127.0.0.1:{Me.getPort()}"))
            
        except Exception as e:
            self.root.after(0, lambda: self._handleStartError(e))
    
    def _updateStartButtonState(self):
        """開始ボタンの状態を更新"""
        self.startButton.config(state=tk.DISABLED)
        self.stopButton.config(state=tk.NORMAL)
    
    def _handleStartError(self, error):
        """開始エラーを処理"""
        messagebox.showerror("エラー", f"ノードの開始に失敗しました: {str(error)}")
        self.logMessage(f"エラー: {str(error)}")
        self.startButton.config(state=tk.NORMAL)
        self.stopButton.config(state=tk.DISABLED)
    
    def stopNode(self):
        """ノードを停止（非同期）"""
        # ボタンを即座に無効化
        self.stopButton.config(state=tk.DISABLED)
        self.logMessage("ノード停止中...")
        
        # 非同期でノード停止処理を実行
        self.runAsync(self._stopNodeInternal)
    
    def _stopNodeInternal(self):
        """ノード停止の内部処理"""
        try:
            self.isRunning = False
            Me.sockClose()
            
            # GUIスレッドでボタン状態を更新
            self.root.after(0, self._updateStopButtonState)
            
            self.logMessage("ノードを停止しました")
            
        except Exception as e:
            self.root.after(0, lambda: self._handleStopError(e))
    
    def _updateStopButtonState(self):
        """停止ボタンの状態を更新"""
        self.startButton.config(state=tk.NORMAL)
        self.stopButton.config(state=tk.DISABLED)
    
    def _handleStopError(self, error):
        """停止エラーを処理"""
        messagebox.showerror("エラー", f"ノードの停止に失敗しました: {str(error)}")
        self.logMessage(f"エラー: {str(error)}")
        self.startButton.config(state=tk.NORMAL)
        self.stopButton.config(state=tk.DISABLED)
    
    def addInitialNode(self):
        """初期ノードを追加（非同期）"""
        if not self.isRunning:
            messagebox.showwarning("警告", "先にノードを開始してください")
            return
        
        nodeInput = self.nodeInput.get().strip()
        if not nodeInput:
            messagebox.showwarning("警告", "Idを入力してください")
            return
        
        # 非同期でノード追加処理を実行
        self.runAsync(self._addInitialNodeInternal, nodeInput)
    
    def _addInitialNodeInternal(self, nodeInput):
        """初期ノード追加の内部処理"""
        try:
            self.logMessage(f"ノード追加処理開始: {nodeInput}")
            
            # ノードIDからノードを作成
            nodeIAndP = nodeTrans.nodeIAndPFromId(nodeInput)
            self.logMessage(f"ノードIP:Port解析結果: {nodeIAndP}")
            
            fNode = Node.nodeFromIAndP(nodeIAndP)
            if not fNode:
                self.root.after(0, lambda: messagebox.showerror("エラー", "無効なノードIDです"))
                self.logMessage(f"ノード作成失敗: {nodeInput}")
                return
            
            self.logMessage(f"ノード作成成功: {fNode.getNodeInfo().ip}:{fNode.getNodeInfo().port}")
            
            # ノードにhelloを送信
            self.logMessage("Hello送信中...")
            if fNode.hello():
                self.logMessage("Hello成功、ノードを登録中...")
                Nodes.registerNode(fNode)
                self.logMessage(f"初期ノードを追加しました: {nodeInput}")
                self.logMessage(f"ノード名: {fNode.getNodeInfo().name}")
                self.logMessage(f"現在の登録ノード数: {len(Nodes.getNodes())}")
                
                # ノード追加後に即座にノードリストを更新
                self.root.after(0, self.updateNodeInfo)
                
                # 入力フィールドをクリア
                self.root.after(0, lambda: self.nodeInput.delete(0, tk.END))
            else:
                self.root.after(0, lambda: messagebox.showerror("エラー", "ノードとの接続に失敗しました"))
                self.logMessage(f"接続失敗: {nodeInput}")
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("エラー", f"ノードの追加に失敗しました: {str(e)}"))
            self.logMessage(f"エラー: {str(e)}")
            import traceback
            self.logMessage(f"詳細エラー: {traceback.format_exc()}")
    
    def updateNodeInfo(self):
        """ノード情報を更新（非同期）"""
        # 常にノード情報を更新
        if self.isRunning:
            # 非同期で更新処理を実行
            self.runAsync(self._updateNodeInfoInternal)
        else:
            # ノードが停止中の場合は基本情報のみ表示
            self.myInfoText.set("ノードが開始されていません")
            self.root.after(0, lambda: self._updateNodesTree([]))
    
    def _updateNodeInfoInternal(self):
        """ノード情報更新の内部処理"""
        try:
            from src.manager.Nodes import Nodes
            
            # 自分のノード情報を更新
            myId = Me.getMyId()
            myInfo = f"ノード名: {Me.getName()} | ポート: {Me.getPort()} | ID: {myId}"
            
            # GUIスレッドで更新
            self.root.after(0, lambda: self.myInfoText.set(myInfo))
            
            # 接続ノード一覧を更新
            nodes = Nodes.getNodes()
            
            nodes_data = []
            for node in nodes:
                try:
                    nodeInfo = node.getNodeInfo()
                    nodeIdStr = nodeTrans.idFromNodeIAndP(f"{nodeInfo.ip}:{nodeInfo.port}")
                    
                    # BAN状態を確認
                    status = "BAN" if Nodes.isBannedNodeId(nodeIdStr) else "接続中"
                    
                    nodes_data.append((
                        nodeIdStr,
                        nodeInfo.name or "不明",
                        nodeInfo.pubKey[:20] + "..." if len(nodeInfo.pubKey) > 20 else nodeInfo.pubKey,
                        status
                    ))
                except:
                    pass
            
            # GUIスレッドでノード一覧を更新
            self.root.after(0, lambda: self._updateNodesTree(nodes_data))
            
        except Exception as e:
            self.logMessage(f"情報更新エラー: {str(e)}")
            self.logMessage(f"詳細エラー: {traceback.format_exc()}")
    
    def _updateNodesTree(self, nodes_data):
        """ノードツリーを更新"""
        self.nodesTree.delete(*self.nodesTree.get_children())
        for node_data in nodes_data:
            self.nodesTree.insert("", tk.END, values=node_data)
    
    def manualUpdate(self):
        """手動でノードリストを更新"""
        self.updateNodeInfo()
    
    def updateMessages(self):
        """メッセージ一覧を更新（非同期）"""
        # 常にメッセージリストを更新（ノードが停止中でも）
        if self.isRunning:
            self.runAsync(self._updateMessagesInternal)
        else:
            # ノードが停止中の場合は空のリストを表示
            self.messagesData = []
            self.root.after(0, lambda: self._updateMessagesListbox())
    
    def _updateMessagesInternal(self):
        """メッセージ更新の内部処理（SNS風）"""
        try:
            # メッセージを階層構造で整理
            self.messagesData = self.organizeMessages()
            
            # GUIスレッドでメッセージ一覧を更新
            self.root.after(0, lambda: self._updateMessagesListbox())
                
        except Exception as e:
            self.logMessage(f"メッセージ更新エラー: {str(e)}")
    
    def organizeMessages(self):
        """メッセージを階層構造で整理"""
        try:
            from itertools import chain
            from src.manager.OthersMessages import OthersMessages
            from src.manager.MyMessages import MyMessages
            
            # ルートメッセージとリプライを分類
            root_messages = []
            reply_messages = []
            
            for message in chain(OthersMessages.getMessages(), MyMessages.getMessages()):
                if isinstance(message, RootMessage):
                    root_messages.append(message)
                elif isinstance(message, ReplyMessage):
                    reply_messages.append(message)
            
            # ルートメッセージを時刻順にソート（新しい順）
            root_messages.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 各ルートメッセージに対してリプライを関連付け
            organized_messages = []
            
            for root_msg in root_messages:
                # このルートメッセージへのリプライを検索
                replies = []
                for reply in reply_messages:
                    if reply.fromHash == root_msg.hash():
                        replies.append(reply)
                
                # リプライを時刻順にソート
                replies.sort(key=lambda x: x.timestamp)
                
                organized_messages.append({
                    'root': root_msg,
                    'replies': replies
                })
            
            return organized_messages
            
        except Exception as e:
            self.logMessage(f"メッセージ整理エラー: {str(e)}")
            return []
    
    def _updateMessagesListbox(self):
        """メッセージリストボックスを更新"""
        self.messagesListbox.delete(0, tk.END)
        
        for msg_data in self.messagesData:
            root_msg = msg_data['root']
            replies = msg_data['replies']
            
            # タイムスタンプを読みやすい形式に変換
            timestamp = datetime.fromtimestamp(root_msg.timestamp).strftime("%m/%d %H:%M")
            
            # 送信者名を取得
            sender = "自分" if root_msg.author is None else (root_msg.author.getNodeInfo().name or "不明")
            
            # 内容を短縮（長すぎる場合）
            content = root_msg.content
            if len(content) > 60:
                content = content[:57] + "..."
            
            # リプライ数を表示
            reply_count = len(replies)
            reply_text = f" ({reply_count}件)" if reply_count > 0 else ""
            
            # リストボックスに表示するテキスト
            display_text = f"[{timestamp}] {sender}: {content}{reply_text}"
            
            self.messagesListbox.insert(tk.END, display_text)
    
    def setupTrafficTab(self):
        """トラフィックタブの設定"""
        trafficTab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(trafficTab, text="トラフィック")
        trafficTab.columnconfigure(0, weight=1)
        trafficTab.rowconfigure(0, weight=1)

        # トラフィック一覧
        columns = ("IP", "通信量(MB)")
        self.trafficTree = ttk.Treeview(trafficTab, columns=columns, show="headings", height=20)
        for col in columns:
            self.trafficTree.heading(col, text=col)
            self.trafficTree.column(col, width=200)
        self.trafficTree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        trafficScrollbar = ttk.Scrollbar(trafficTab, orient=tk.VERTICAL, command=self.trafficTree.yview)
        self.trafficTree.configure(yscrollcommand=trafficScrollbar.set)
        trafficScrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # BANボタン
        trafficBtnFrame = ttk.Frame(trafficTab)
        trafficBtnFrame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(trafficBtnFrame, text="選択IPをBAN", command=self.banSelectedTrafficIp).pack(side=tk.LEFT, padx=5)

    def banSelectedTrafficIp(self):
        """トラフィック一覧から選択IPをBAN"""
        selection = self.trafficTree.selection()
        if not selection:
            messagebox.showwarning("警告", "BANするIPを選択してください")
            return
        try:
            item = selection[0]
            ip = self.trafficTree.item(item, "values")[0]
            from src.manager.Nodes import Nodes
            if Nodes.isBannedIp(ip):
                messagebox.showinfo("情報", "このIPは既にBANされています")
                return
            Nodes.banIp(ip)
            self.logMessage(f"IP {ip} をBANしました")
            # BANしたIPのノードも切断
            nodes = Nodes.getNodesFromIp(ip)
            for node in nodes:
                nodeIdStr = node.idFromNodeIAndP(f"{node.getNodeInfo().ip}:{node.getNodeInfo().port}")
                self.disconnectNode(nodeIdStr)
            self.updateTrafficInfo()
        except Exception as e:
            messagebox.showerror("エラー", f"IPのBANに失敗しました: {str(e)}")
            self.logMessage(f"エラー: {str(e)}")

    def updateTrafficInfo(self):
        """トラフィック情報を更新"""
        try:
            from src.manager.Nodes import Nodes
            traffics = Nodes.traffics()
            # MB単位に変換
            self.trafficData = []
            for ip, byte in traffics.items():
                mb = round(byte / (1024 * 1024), 3)
                self.trafficData.append((ip, mb))
            self.root.after(0, self._updateTrafficTree)
        except Exception as e:
            self.logMessage(f"トラフィック情報更新エラー: {str(e)}")

    def _updateTrafficTree(self):
        self.trafficTree.delete(*self.trafficTree.get_children())
        for row in self.trafficData:
            self.trafficTree.insert("", tk.END, values=row)

    def scheduleUpdate(self):
        """定期的な更新をスケジュール"""
        self.updateNodeInfo()
        self.updateMessages()
        self.updateTrafficInfo()  # 追加
        self.root.after(self.updateInterval, self.scheduleUpdate)

    def sendMessage(self):
        """メッセージを送信（非同期）"""
        if not self.isRunning:
            messagebox.showwarning("警告", "先にノードを開始してください")
            return

        messageContent = self.messageInput.get().strip()
        if not messageContent:
            messagebox.showwarning("警告", "メッセージを入力してください")
            return

        # リプライかどうか判定して非同期送信
        if self.selectedMessage:
            root_msg = self.selectedMessage['root']
            # 自分自身にはリプライできないようにする
            if root_msg.author is None:
                messagebox.showwarning("警告", "自分のメッセージにはリプライできません")
                return
            self.runAsync(self._sendMessageInternal, messageContent, root_msg)
        else:
            self.runAsync(self._sendMessageInternal, messageContent, None)

    def _sendMessageInternal(self, messageContent, replyToRootMsg=None):
        """メッセージ送信の内部処理（リプライ対応）"""
        try:
            if replyToRootMsg:
                # リプライとして投稿
                from src.model.Message import ReplyMessage
                timestamp = int(time.time())
                replyMsg = ReplyMessage(
                    content=messageContent,
                    timestamp=timestamp,
                    fromHash=replyToRootMsg.hash(),
                    fromNode=replyToRootMsg.author
                )
                MyMessages.addMessage(replyMsg)
                self.logMessage(f"リプライを送信しました: {messageContent}")
            else:
                # ルートメッセージとして投稿
                timestamp = int(time.time())
                rootMessage = RootMessage(
                    content=messageContent,
                    timestamp=timestamp
                )
                MyMessages.addMessage(rootMessage)
                self.logMessage(f"メッセージを送信しました: {messageContent}")

            # GUIスレッドで入力フィールドをクリア
            self.root.after(0, lambda: self.messageInput.delete(0, tk.END))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("エラー", f"メッセージの送信に失敗しました: {str(e)}"))
            self.logMessage(f"エラー: {str(e)}")

    def banSelectedNode(self):
        """選択されたノードをBAN"""
        selection = self.nodesTree.selection()
        if not selection:
            messagebox.showwarning("警告", "BANするノードを選択してください")
            return
        
        try:
            item = selection[0]
            nodeId = self.nodesTree.item(item, "values")[0]
            
            from src.manager.Nodes import Nodes
            
            if Nodes.isBannedNodeId(nodeId):
                messagebox.showinfo("情報", "このノードは既にBANされています")
                return
            
            # NodesクラスでBAN処理
            Nodes.banNodeId(nodeId)
            
            # ノードを切断
            self.disconnectNode(nodeId)
            
            self.logMessage(f"ノード {nodeId} をBANしました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"ノードのBANに失敗しました: {str(e)}")
            self.logMessage(f"エラー: {str(e)}")
    
    def unbanSelectedNode(self):
        """選択されたノードのBANを解除"""
        selection = self.nodesTree.selection()
        if not selection:
            messagebox.showwarning("警告", "BAN解除するノードを選択してください")
            return
        
        try:
            item = selection[0]
            nodeId = self.nodesTree.item(item, "values")[0]
            
            from src.manager.Nodes import Nodes
            
            if not Nodes.isBannedNodeId(nodeId):
                messagebox.showinfo("情報", "このノードはBANされていません")
                return
            
            # NodesクラスでBAN解除処理
            Nodes.unbanNodeId(nodeId)
            
            self.logMessage(f"ノード {nodeId} のBANを解除しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"ノードのBAN解除に失敗しました: {str(e)}")
            self.logMessage(f"エラー: {str(e)}")
    
    def showBanList(self):
        """BANリストを表示"""
        from src.manager.Nodes import Nodes
        bannedNodeIds = Nodes.getBannedNodeIds()
        
        if not bannedNodeIds:
            messagebox.showinfo("BANリスト", "BANされたノードはありません")
            return
        
        banList = "\n".join(sorted(bannedNodeIds))
        messagebox.showinfo("BANリスト", f"BANされたノード:\n{banList}")
    
    def disconnectNode(self, nodeId):
        """指定されたノードを切断"""
        try:
            from src.manager.Nodes import Nodes
            from manager.OthersMessages import OthersMessages
            
            # ノードIDからノード情報を取得
            node = Nodes.getNodeFromId(nodeId)
            if node:
                nodeInfo = node.getNodeInfo()
                
                # ノードを削除
                if Nodes.removeNodeById(nodeId):
                    # 該当IPのメッセージも削除
                    OthersMessages.deleteMessagesFromIp(nodeInfo.ip)
                    self.logMessage(f"ノード {nodeId} を切断しました")
                else:
                    self.logMessage(f"ノード {nodeId} の切断に失敗しました")
            else:
                self.logMessage(f"ノード {nodeId} が見つかりません")
                
        except Exception as e:
            self.logMessage(f"ノード切断エラー: {str(e)}")
    
    def clearLog(self):
        """ログをクリア"""
        self.logText.delete(1.0, tk.END)
        self.logMessage("ログをクリアしました")
    
    def saveLog(self):
        """ログをファイルに保存"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="ログを保存"
            )
            if filename:
                with open(filename, 'w', encoding=ENCODE) as f:
                    f.write(self.logText.get(1.0, tk.END))
                self.logMessage(f"ログを保存しました: {filename}")
        except Exception as e:
            messagebox.showerror("エラー", f"ログの保存に失敗しました: {str(e)}")

def main():
    root = tk.Tk()
    app = TuneGui(root)
    
    # アプリケーション終了時の処理
    def onClosing():
        if app.isRunning:
            app.stopNode()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", onClosing)
    root.mainloop()

if __name__ == "__main__":
    main()