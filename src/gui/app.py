"""Write by Cursor"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import os
import sys
import traceback
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.net.Me import Me
from src.manager.Nodes import Nodes
from src.manager.Messages import Messages
from src.net.Node import Node
from src.model.NodeInfo import NodeInfo
from src.model.Message import RootMessage, ReplyMessage
from src.util import nodeId

class TuneGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Tune - P2P Network Node Manager")
        self.root.geometry("1200x800")
        
        # ノード名の設定
        self.nodeName = tk.StringVar(value="MyNode")
        
        # 最大ノード数設定
        from src.manager.Nodes import Nodes
        self.maxNodes = tk.IntVar(value=Nodes.getMaxNodes())
        
        # BANされたノードのリスト（GUI用、実際のBAN状態はNodesクラスで管理）
        self.bannedNodes = set()
        
        # GUIの初期化
        self.setupGui()
        
        # ノードの状態
        self.isRunning = False
        self.serveThread = None
        self.syncerThread = None
        
        # 定期的な更新
        self.updateInterval = 2000  # 2秒
        self.scheduleUpdate()
    
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
        
        # 最大ノード数設定
        ttk.Label(basicFrame, text="最大ノード数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        maxNodesFrame = ttk.Frame(basicFrame)
        maxNodesFrame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        maxNodesSpinbox = ttk.Spinbox(maxNodesFrame, from_=1, to=100, textvariable=self.maxNodes, width=10)
        maxNodesSpinbox.pack(side=tk.LEFT)
        
        ttk.Button(maxNodesFrame, text="設定", command=self.setMaxNodes).pack(side=tk.LEFT, padx=5)
        
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
        
        # メッセージツリービュー
        msgColumns = ("時刻", "タイプ", "内容", "送信者")
        self.messagesTree = ttk.Treeview(messagesFrame, columns=msgColumns, show="headings", height=20)
        
        for col in msgColumns:
            self.messagesTree.heading(col, text=col)
            self.messagesTree.column(col, width=150)
        
        msgScrollbar = ttk.Scrollbar(messagesFrame, orient=tk.VERTICAL, command=self.messagesTree.yview)
        self.messagesTree.configure(yscrollcommand=msgScrollbar.set)
        
        self.messagesTree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        msgScrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
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
    
    def logMessage(self, message):
        """ログにメッセージを追加"""
        timestamp = time.strftime("%H:%M:%S")
        self.logText.insert(tk.END, f"[{timestamp}] {message}\n")
        self.logText.see(tk.END)
    
    def startNode(self):
        """ノードを開始"""
        try:
            # ノード名を設定
            Me.setName(self.nodeName.get())
            
            # スレッドを開始
            self.serveThread = threading.Thread(target=Me.serve, daemon=True)
            self.syncerThread = threading.Thread(target=Me.syncer, args=(10,), daemon=True)
            
            self.serveThread.start()
            self.syncerThread.start()
            
            self.isRunning = True
            self.startButton.config(state=tk.DISABLED)
            self.stopButton.config(state=tk.NORMAL)
            
            self.logMessage(f"ノード '{self.nodeName.get()}' を開始しました")
            self.logMessage(f"ポート: {Me.getPort()}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"ノードの開始に失敗しました: {str(e)}")
            self.logMessage(f"エラー: {str(e)}")
    
    def stopNode(self):
        """ノードを停止"""
        try:
            self.isRunning = False
            Me.sockClose()
            
            self.startButton.config(state=tk.NORMAL)
            self.stopButton.config(state=tk.DISABLED)
            
            self.logMessage("ノードを停止しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"ノードの停止に失敗しました: {str(e)}")
            self.logMessage(f"エラー: {str(e)}")
    
    def addInitialNode(self):
        """初期ノードを追加"""
        if not self.isRunning:
            messagebox.showwarning("警告", "先にノードを開始してください")
            return
        
        nodeInput = self.nodeInput.get().strip()
        if not nodeInput:
            messagebox.showwarning("警告", "Idを入力してください")
            return
        
        try:
            # ノードIDからノードを作成
            fNode = Node.nodeFromIAndP(nodeId.nodeIAndPFromId(nodeInput))
            if not fNode:
                messagebox.showerror("エラー", "無効なノードIDです")
                return
            
            # ノードにhelloを送信
            if fNode.hello():
                Nodes.registerNode(fNode)
                self.logMessage(f"初期ノードを追加しました: {nodeInput}")
                self.logMessage(f"ノード名: {fNode.getNodeInfo().name}")
            else:
                messagebox.showerror("エラー", "ノードとの接続に失敗しました")
                self.logMessage(f"接続失敗: {nodeInput}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"ノードの追加に失敗しました: {str(e)}")
            self.logMessage(f"エラー: {str(e)}")
    
    def sendMessage(self):
        """メッセージを送信"""
        if not self.isRunning:
            messagebox.showwarning("警告", "先にノードを開始してください")
            return
        
        messageContent = self.messageInput.get().strip()
        if not messageContent:
            messagebox.showwarning("警告", "メッセージを入力してください")
            return
        
        try:
            # ルートメッセージを作成
            timestamp = int(time.time())
            rootMessage = RootMessage(
                content=messageContent,
                timestamp=timestamp
            )
            
            # メッセージを追加
            Messages.addMessage(rootMessage)
            
            # 入力フィールドをクリア
            self.messageInput.delete(0, tk.END)
            
            self.logMessage(f"メッセージを送信しました: {messageContent}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"メッセージの送信に失敗しました: {str(e)}")
            self.logMessage(f"エラー: {str(e)}")
    
    def setMaxNodes(self):
        """最大ノード数を設定"""
        try:
            maxNodes = self.maxNodes.get()
            if maxNodes < 1:
                messagebox.showwarning("警告", "最大ノード数は1以上である必要があります")
                return
            
            # 最大ノード数を設定
            from src.manager.Nodes import Nodes
            Nodes.setMaxNodes(maxNodes)
            
            self.logMessage(f"最大ノード数を {maxNodes} に設定しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"最大ノード数の設定に失敗しました: {str(e)}")
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
            from src.manager.Messages import Messages
            
            # ノードIDからノード情報を取得
            node = Nodes.getNodeFromId(nodeId)
            if node:
                nodeInfo = node.getNodeInfo()
                
                # ノードを削除
                if Nodes.removeNodeById(nodeId):
                    # 該当IPのメッセージも削除
                    Messages.deleteMessagesFromIp(nodeInfo.ip)
                    self.logMessage(f"ノード {nodeId} を切断しました")
                else:
                    self.logMessage(f"ノード {nodeId} の切断に失敗しました")
            else:
                self.logMessage(f"ノード {nodeId} が見つかりません")
                
        except Exception as e:
            self.logMessage(f"ノード切断エラー: {str(e)}")
    
    def updateNodeInfo(self):
        """ノード情報を更新"""
        if self.isRunning:
            try:
                from src.manager.Nodes import Nodes
                
                # 自分のノード情報を更新
                myId = Me.getMyId()
                myInfo = f"ノード名: {Me.getName()} | ポート: {Me.getPort()} | ID: {myId}"
                self.myInfoText.set(myInfo)
                
                # 接続ノード一覧を更新
                self.nodesTree.delete(*self.nodesTree.get_children())
                
                for node in Nodes.getNodes():
                    nodeInfo = node.getNodeInfo()
                    nodeIdStr = nodeId.idFromNodeIAndP(f"{nodeInfo.ip}:{nodeInfo.port}")
                    
                    # BAN状態を確認
                    status = "BAN" if Nodes.isBannedNodeId(nodeIdStr) else "接続中"
                    
                    self.nodesTree.insert("", tk.END, values=(
                        nodeIdStr,
                        nodeInfo.name or "不明",
                        nodeInfo.pubKey[:20] + "..." if len(nodeInfo.pubKey) > 20 else nodeInfo.pubKey,
                        status
                    ))
                
                # メッセージ一覧を更新
                self.updateMessages()
                
            except Exception as e:
                print(traceback.format_exc())
                self.logMessage(f"情報更新エラー: {str(e)}")
        else:
            self.myInfoText.set("ノードが開始されていません")
            self.nodesTree.delete(*self.nodesTree.get_children())
            self.messagesTree.delete(*self.messagesTree.get_children())
    
    def updateMessages(self):
        """メッセージ一覧を更新"""
        try:
            self.messagesTree.delete(*self.messagesTree.get_children())
            
            for message in Messages.getMessages():
                # タイムスタンプを読みやすい形式に変換
                timestamp = datetime.fromtimestamp(message.timestamp).strftime("%H:%M:%S")
                
                # メッセージタイプを判定
                if isinstance(message, RootMessage):
                    msgType = "ルート"
                    sender = "自分" if message.author is None else "不明"
                elif isinstance(message, ReplyMessage):
                    msgType = "返信"
                    sender = message.fromNode.getNodeInfo().name or "不明"
                else:
                    msgType = "不明"
                    sender = "不明"
                
                # 内容を短縮（長すぎる場合）
                content = message.content
                if len(content) > 50:
                    content = content[:47] + "..."
                
                self.messagesTree.insert("", tk.END, values=(
                    timestamp,
                    msgType,
                    content,
                    sender
                ))
                
        except Exception as e:
            self.logMessage(f"メッセージ更新エラー: {str(e)}")
    
    def scheduleUpdate(self):
        """定期的な更新をスケジュール"""
        self.updateNodeInfo()
        self.root.after(self.updateInterval, self.scheduleUpdate)

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
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.logText.get(1.0, tk.END))
                self.logMessage(f"ログを保存しました: {filename}")
        except Exception as e:
            messagebox.showerror("エラー", f"ログの保存に失敗しました: {str(e)}")

def main():
    # データベースディレクトリを作成
    os.makedirs("dbs", exist_ok=True)
    
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