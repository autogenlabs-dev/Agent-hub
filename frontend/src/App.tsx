import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from '@/components/layout';
import Dashboard from '@/pages/dashboard';
import Agents from '@/pages/agents';
import Tasks from '@/pages/tasks';
import Messages from '@/pages/messages';
import Memory from '@/pages/memory';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="agents" element={<Agents />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="messages" element={<Messages />} />
          <Route path="memory" element={<Memory />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;