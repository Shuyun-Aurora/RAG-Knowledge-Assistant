// 课程数据
export const courses = [
  { 
    id: '1', 
    name: '人工智能导论', 
    teacher: '张教授', 
    description: '本课程介绍人工智能的基本概念、发展历程和主要应用领域。内容涵盖人工智能的历史、主要分支（如机器学习、深度学习、自然语言处理、计算机视觉等）、典型应用场景（如智能推荐、自动驾驶、语音识别等），并结合实际案例帮助学生理解AI技术在现实中的应用。课程还将介绍AI伦理、发展趋势及未来挑战，适合对人工智能感兴趣的同学选修。',
    students: 156,
    progress: 75,
    materials: [
      { name: '第一章：AI概述.pdf', size: '2.5MB', type: 'pdf', uploadTime: '2024-01-10' },
      { name: '第二章：机器学习基础.pptx', size: '8.2MB', type: 'ppt', uploadTime: '2024-01-12' },
      { name: '课程大纲.docx', size: '1.2MB', type: 'doc', uploadTime: '2024-01-08' },
      { name: '参考书目.pdf', size: '3.1MB', type: 'pdf', uploadTime: '2024-01-09' },
      { name: '实验指导书.pdf', size: '5.6MB', type: 'pdf', uploadTime: '2024-01-11' }
    ],
    exercises: [
      { id: 'ex1', question: '什么是人工智能？请简述其发展历程。', type: '简答题', difficulty: '简单', dueDate: '2024-01-20' },
      { id: 'ex2', question: '机器学习的主要类型有哪些？请举例说明。', type: '多选题', difficulty: '中等', dueDate: '2024-01-25' },
      { id: 'ex3', question: '请设计一个简单的神经网络结构。', type: '编程题', difficulty: '困难', dueDate: '2024-01-30' }
    ]
  },
  { 
    id: '2', 
    name: '数据结构与算法', 
    teacher: '李教授', 
    description: '本课程系统讲解数据结构的基本概念、常用类型（如数组、链表、栈、队列、树、图等）及其在算法设计中的应用。内容包括算法复杂度分析、递归与分治、排序与查找、图的遍历等。通过理论讲解与编程实践相结合，帮助学生掌握高效解决实际问题的方法。适合有一定编程基础、希望提升算法能力的同学选修。',
    students: 203,
    progress: 60,
    materials: [
      { name: '第一章：线性表.pdf', size: '3.2MB', type: 'pdf', uploadTime: '2024-01-05' },
      { name: '第二章：栈和队列.pptx', size: '6.8MB', type: 'ppt', uploadTime: '2024-01-08' },
      { name: '课程大纲.docx', size: '1.5MB', type: 'doc', uploadTime: '2024-01-03' },
      { name: '算法复杂度分析.pdf', size: '2.8MB', type: 'pdf', uploadTime: '2024-01-10' }
    ],
    exercises: [
      { id: 'ex1', question: '请实现一个栈的基本操作。', type: '编程题', difficulty: '简单', dueDate: '2024-01-18' },
      { id: 'ex2', question: '分析快速排序的时间复杂度。', type: '简答题', difficulty: '中等', dueDate: '2024-01-22' }
    ]
  }
];

// 用户数据
export const users = [
  { id: 't1', username: 'teacher1', password: '123456', role: 'teacher', name: '张教授' },
  { id: 't2', username: 'teacher2', password: '123456', role: 'teacher', name: '李教授' },
  { id: 's1', username: 'student1', password: '123456', role: 'student', name: '小明' },
  { id: 's2', username: 'student2', password: '123456', role: 'student', name: '小红' },
  { id: 's3', username: 'student3', password: '123456', role: 'student', name: '小华' }
];

// 讨论数据
export const discussions = {
  '1': [
    {
      id: 'p1',
      title: '人工智能导论课程欢迎贴',
      author: '张教授',
      avatar: '张',
      isAnonymous: false,
      content: '欢迎大家来到人工智能导论课程社区！有问题随时发帖讨论。',
      time: '2024-01-15 09:00',
      comments: [
        { user: '小明', avatar: '明', content: '老师，这门课程需要什么基础吗？', time: '2024-01-15 09:30' },
        { user: '张教授', avatar: '张', content: '建议有基本的数学和编程基础，我们会从基础开始讲解。', time: '2024-01-15 10:00' }
      ]
    },
    {
      id: 'p2',
      title: '作业提交时间讨论',
      author: '小红',
      avatar: '红',
      isAnonymous: false,
      content: '请问作业什么时候交？',
      time: '2024-01-15 14:20',
      comments: [
        { user: '张教授', avatar: '张', content: '每周五晚上12点前提交，逾期不候。', time: '2024-01-15 15:00' }
      ]
    },
    {
      id: 'p3',
      title: '匿名吐槽区',
      author: '匿名',
      avatar: '?',
      isAnonymous: true,
      content: '人工智能导论的实验好多啊，有没有一起组队的？',
      time: '2024-01-16 11:20',
      comments: []
    }
  ],
  '2': [
    {
      id: 'p1',
      title: '数据结构课程交流',
      author: '李教授',
      avatar: '李',
      isAnonymous: false,
      content: '数据结构是计算机科学的基础，希望大家认真学习。',
      time: '2024-01-10 08:30',
      comments: [
        { user: '小华', avatar: '华', content: '老师，能推荐一些学习资料吗？', time: '2024-01-10 10:15' },
        { user: '李教授', avatar: '李', content: '可以参考《算法导论》和《数据结构与算法分析》。', time: '2024-01-10 11:00' }
      ]
    },
    {
      id: 'p2',
      title: '算法难点求助',
      author: '小华',
      avatar: '华',
      isAnonymous: false,
      content: '有同学能讲讲图的遍历算法吗？',
      time: '2024-01-12 15:40',
      comments: []
    }
  ]
};

// 智能问答历史数据
export const qaHistory = {
  '1': [
    { type: 'question', content: '什么是机器学习？', time: '2024-01-14 16:30', user: '小明' },
    { type: 'answer', content: '机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习和改进。', time: '2024-01-14 16:31', user: 'AI助手' },
    { type: 'question', content: '深度学习与传统机器学习有什么区别？', time: '2024-01-13 10:15', user: '小红' },
    { type: 'answer', content: '深度学习使用多层神经网络，能够自动学习特征，而传统机器学习需要手动特征工程。', time: '2024-01-13 10:16', user: 'AI助手' }
  ],
  '2': [
    { type: 'question', content: '什么是时间复杂度？', time: '2024-01-12 14:20', user: '小华' },
    { type: 'answer', content: '时间复杂度是衡量算法执行时间随输入规模增长的变化趋势。', time: '2024-01-12 14:21', user: 'AI助手' }
  ]
};

// 知识图谱数据（模拟）
export const knowledgeGraphs = {
  '1': {
    nodes: [
      { id: 'ai', label: '人工智能', group: 1 },
      { id: 'ml', label: '机器学习', group: 1 },
      { id: 'dl', label: '深度学习', group: 1 },
      { id: 'nn', label: '神经网络', group: 1 },
      { id: 'cv', label: '计算机视觉', group: 2 },
      { id: 'nlp', label: '自然语言处理', group: 2 }
    ],
    edges: [
      { from: 'ai', to: 'ml' },
      { from: 'ml', to: 'dl' },
      { from: 'dl', to: 'nn' },
      { from: 'ai', to: 'cv' },
      { from: 'ai', to: 'nlp' }
    ]
  },
  '2': {
    nodes: [
      { id: 'ds', label: '数据结构', group: 1 },
      { id: 'array', label: '数组', group: 1 },
      { id: 'list', label: '链表', group: 1 },
      { id: 'stack', label: '栈', group: 1 },
      { id: 'queue', label: '队列', group: 1 },
      { id: 'tree', label: '树', group: 2 },
      { id: 'graph', label: '图', group: 2 }
    ],
    edges: [
      { from: 'ds', to: 'array' },
      { from: 'ds', to: 'list' },
      { from: 'ds', to: 'stack' },
      { from: 'ds', to: 'queue' },
      { from: 'ds', to: 'tree' },
      { from: 'ds', to: 'graph' }
    ]
  }
};

// Banner轮播数据
export const bannerData = [
  {
    img: 'https://img.remit.ee/api/file/BQACAgUAAyEGAASHRsPbAAImVWhc8Su4goN4MuMgnBVE38EwyYa-AAKkFgACvxDoVrSO_4TzL6PNNgQ.jpg',
    title: '欢迎来到课程智能助手',
    desc: '智能学习，轻松掌握每一门课程'
  },
  {
    img: 'https://img.remit.ee/api/file/BQACAgUAAyEGAASHRsPbAAIr42hl6BF0JVXjOL-LHYMGmQ6Q5ENuAAKrGAACPnsxV1FPhaeIkU1_NgQ.jpg',
    title: '优质课程推荐',
    desc: '发现更多优质课程，提升自我'
  },
  {
    img: 'https://img.remit.ee/api/file/BQACAgUAAyEGAASHRsPbAAIr5Ghl6BK3LFz4QREYh9WqwauCbnptAAKsGAACPnsxV25CLs0-gab8NgQ.jpg',
    title: '智能问答与知识图谱',
    desc: 'AI助力，答疑解惑，知识一网打尽'
  }
]; 