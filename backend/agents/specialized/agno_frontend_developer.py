"""
Frontend Developer Agent

The Frontend Developer agent implements UI features, components, and integrations
with the backend API. Specializes in React/Next.js development.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig, AgentResponse
from backend.schemas.agent_message import (
    StatusUpdate,
    Question,
    CodeReviewRequest,
    TaskCompletion,
)


class AgnoFrontendDeveloperAgent(AgnoSquadAgent):
    """
    Frontend Developer Agent (Agno-Powered) - UI Implementation Specialist

    Responsibilities:
    - Implement frontend features (React/Next.js components)
    - Integrate with backend APIs
    - Ensure responsive design
    - Write component tests
    - Follow design system guidelines
    - Optimize performance
    - Handle state management
    - Implement accessibility features

    Note: In Phase 4, this agent will use MCP servers to actually
    read/write code. For Phase 3, it plans and provides guidance.
    """

    def get_capabilities(self) -> List[str]:
        """
        Return list of Frontend Developer capabilities

        Returns:
            List of capability names
        """
        return [
            "analyze_task",
            "plan_implementation",
            "design_components",
            "write_components",  # Phase 4: via MCP
            "integrate_api",
            "write_tests",  # Phase 4: via MCP
            "ensure_responsive",
            "optimize_performance",
            "ask_question",
            "provide_status_update",
            "request_code_review",
            "request_design_review",
        ]

    async def analyze_task(
        self,
        task_assignment: Dict[str, Any],
        code_context: Optional[str] = None,
        design_specs: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Analyze assigned frontend task and create implementation plan.

        Args:
            task_assignment: Task assignment from PM
            code_context: Relevant code from RAG
            design_specs: Optional design specifications

        Returns:
            AgentResponse with analysis and plan
        """
        context = {
            "task": task_assignment,
            "code_context": code_context,
            "design_specs": design_specs,
            "action": "task_analysis"
        }

        code_info = ""
        if code_context:
            code_info = f"""
            Existing Components/Patterns:
            {code_context[:2000]}
            """

        design_info = ""
        if design_specs:
            design_info = f"""
            Design Specifications:
            - Figma URL: {design_specs.get('figma_url', 'N/A')}
            - Components: {design_specs.get('components', [])}
            - Colors: {design_specs.get('colors', {})}
            - Breakpoints: {design_specs.get('breakpoints', [])}
            """

        prompt = f"""
        You've been assigned a frontend development task:

        Task: {task_assignment.get('description')}
        Acceptance Criteria:
        {chr(10).join([f'- {c}' for c in task_assignment.get('acceptance_criteria', [])])}

        {code_info}
        {design_info}

        Context:
        {task_assignment.get('context', 'N/A')}

        Please analyze and create an implementation plan:

        1. **UI Requirements**:
           - What UI elements are needed?
           - User interactions?
           - Visual requirements?

        2. **Component Design**:
           - Which components to create/modify?
           - Component hierarchy
           - Props and state
           - Reusability considerations

        3. **API Integration**:
           - Which API endpoints to call?
           - Request/response handling
           - Loading and error states
           - Data transformation

        4. **State Management**:
           - Local state vs global state?
           - Which state management solution?
           - Data flow

        5. **Responsive Design**:
           - Breakpoints to handle
           - Mobile-first approach?
           - Touch interactions?

        6. **Testing Strategy**:
           - Component tests
           - Integration tests
           - Accessibility tests

        7. **Implementation Steps**:
           - Order of implementation
           - Dependencies

        8. **Questions/Clarifications**:
           - What's unclear?
           - Need designer input?
           - Need backend changes?

        Be specific about Next.js/React patterns to use.
        """

        return await self.process_message(prompt, context=context)

    async def design_components(
        self,
        requirements: Dict[str, Any],
        design_system: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Design component structure and interfaces.

        Args:
            requirements: UI requirements
            design_system: Optional design system (colors, spacing, etc.)

        Returns:
            Dictionary with component design
        """
        context = {
            "requirements": requirements,
            "design_system": design_system,
            "action": "component_design"
        }

        design_system_info = ""
        if design_system:
            design_system_info = f"""
            Design System:
            - Components: {design_system.get('components', [])}
            - Colors: {design_system.get('colors', {})}
            - Typography: {design_system.get('typography', {})}
            - Spacing: {design_system.get('spacing', {})}
            """

        prompt = f"""
        Design the component structure:

        Requirements: {requirements}
        {design_system_info}

        Please provide:

        1. **Component Hierarchy**:
           ```
           PageComponent
           ├── HeaderComponent
           ├── MainComponent
           │   ├── SubComponent1
           │   └── SubComponent2
           └── FooterComponent
           ```

        2. **Component Interfaces**:
           For each component:
           - Props (name, type, required/optional)
           - State variables
           - Event handlers
           - Hooks to use

        3. **Data Flow**:
           - How data flows between components
           - Props drilling vs context
           - API calls at which level

        4. **Styling Approach**:
           - Tailwind classes
           - CSS modules
           - Component-specific styles

        5. **Reusability**:
           - Which components are reusable?
           - Shared components to extract?

        6. **File Structure**:
           ```
           components/
           ├── feature/
           │   ├── Component1.tsx
           │   ├── Component2.tsx
           │   └── index.ts
           ```

        Use TypeScript interfaces for props.
        """

        response = await self.process_message(prompt, context=context)

        return {
            "component_design": response.content,
            "components": self._extract_components(response.content),
            "reusable_components": self._extract_reusable(response.content),
        }

    async def integrate_api(
        self,
        api_spec: Dict[str, Any],
        component_context: str,
    ) -> AgentResponse:
        """
        Plan API integration for a component.

        Args:
            api_spec: API specification
            component_context: Component that needs the data

        Returns:
            AgentResponse with integration plan
        """
        context = {
            "api_spec": api_spec,
            "component_context": component_context,
            "action": "api_integration"
        }

        prompt = f"""
        Integrate this API into the component:

        Component: {component_context}

        API Specification:
        - Endpoint: {api_spec.get('endpoint')}
        - Method: {api_spec.get('method')}
        - Request: {api_spec.get('request_schema')}
        - Response: {api_spec.get('response_schema')}
        - Auth: {api_spec.get('auth_required', False)}

        Please provide:

        1. **API Client Setup**:
           - Use React Query? SWR? fetch?
           - Configuration

        2. **Data Fetching**:
           ```typescript
           // Hook or function to call API
           ```

        3. **Loading State**:
           - Show loading spinner?
           - Skeleton UI?
           - Optimistic updates?

        4. **Error Handling**:
           - Error messages
           - Retry logic
           - Fallback UI

        5. **Data Transformation**:
           - Transform response to component format
           - TypeScript interfaces

        6. **Caching Strategy**:
           - Cache duration
           - Revalidation
           - Invalidation triggers

        7. **Auth Handling** (if needed):
           - Token management
           - Refresh token flow

        Use Next.js 14+ patterns (Server Components, Server Actions if appropriate).
        """

        return await self.process_message(prompt, context=context)

    async def ensure_responsive(
        self,
        component: str,
        breakpoints: List[str],
    ) -> AgentResponse:
        """
        Plan responsive design implementation.

        Args:
            component: Component to make responsive
            breakpoints: Breakpoints to support (mobile, tablet, desktop)

        Returns:
            AgentResponse with responsive design plan
        """
        context = {
            "component": component,
            "breakpoints": breakpoints,
            "action": "responsive_design"
        }

        prompt = f"""
        Make this component responsive:

        Component: {component}
        Breakpoints: {', '.join(breakpoints)}

        Please provide:

        1. **Responsive Strategy**:
           - Mobile-first or desktop-first?
           - Progressive enhancement?

        2. **Layout Changes**:
           - Mobile: (describe layout)
           - Tablet: (describe layout)
           - Desktop: (describe layout)

        3. **Tailwind Responsive Classes**:
           ```tsx
           <div className="...">
             // Show how to use sm:, md:, lg: prefixes
           </div>
           ```

        4. **Component Variations**:
           - Different components for different sizes?
           - Or same component with CSS changes?

        5. **Touch Interactions** (mobile):
           - Touch targets (min 44x44px)
           - Swipe gestures?
           - Touch-friendly spacing

        6. **Performance**:
           - Image optimization
           - Lazy loading
           - Code splitting

        7. **Testing**:
           - How to test responsiveness?
           - Breakpoints to test?

        Use Tailwind CSS for responsive design.
        """

        return await self.process_message(prompt, context=context)

    async def optimize_performance(
        self,
        component: str,
        performance_issues: List[str],
    ) -> AgentResponse:
        """
        Optimize component performance.

        Args:
            component: Component to optimize
            performance_issues: Identified performance issues

        Returns:
            AgentResponse with optimization plan
        """
        context = {
            "component": component,
            "issues": performance_issues,
            "action": "performance_optimization"
        }

        issues_str = "\n".join([f"- {issue}" for issue in performance_issues])

        prompt = f"""
        Optimize this component's performance:

        Component: {component}
        Issues Identified:
        {issues_str}

        Please provide optimization strategies:

        1. **React Optimizations**:
           - useMemo for expensive computations?
           - useCallback for functions?
           - React.memo for components?
           - Key prop optimization?

        2. **Rendering Optimizations**:
           - Reduce re-renders
           - Virtual scrolling for lists?
           - Lazy loading components?

        3. **Bundle Size**:
           - Dynamic imports?
           - Code splitting?
           - Tree shaking opportunities?

        4. **Image Optimization**:
           - Next.js Image component
           - Proper sizes and formats
           - Lazy loading

        5. **Data Fetching**:
           - Parallel requests?
           - Request deduplication?
           - Prefetching?

        6. **Measurement**:
           - How to measure improvements?
           - Which metrics to track?

        Focus on Next.js 14+ optimization techniques.
        """

        return await self.process_message(prompt, context=context)

    async def request_design_review(
        self,
        component: str,
        designer_id: UUID,
        implementation_notes: str,
    ) -> Question:
        """
        Request design review from designer.

        Args:
            component: Component name
            designer_id: Designer agent ID
            implementation_notes: Notes about implementation

        Returns:
            Question message for designer
        """
        question = f"""
        I've implemented the {component} component.

        Implementation Notes:
        {implementation_notes}

        Please review:
        1. Does it match the design specs?
        2. Are the spacing and colors correct?
        3. Is the responsive behavior as expected?
        4. Any visual issues?

        Figma link: [insert link]
        Preview link: [insert link]
        """

        return Question(
            task_id=component,
            question=question,
            context=implementation_notes,
            recipient=designer_id,
            urgency="normal",
        )

    # Inherited from BackendDeveloperAgent pattern
    async def provide_status_update(
        self,
        task_id: str,
        status: str,
        progress_percentage: int,
        details: str,
        blockers: Optional[List[str]] = None,
    ) -> StatusUpdate:
        """Provide status update to PM"""
        return StatusUpdate(
            task_id=task_id,
            status=status,
            progress_percentage=progress_percentage,
            details=details,
            blockers=blockers or [],
        )

    async def complete_task(
        self,
        task_id: str,
        pm_id: UUID,
        completion_summary: str,
        deliverables: List[str],
        tests_passed: bool,
        documentation_updated: bool,
    ) -> TaskCompletion:
        """Mark task complete"""
        return TaskCompletion(
            recipient=pm_id,
            task_id=task_id,
            completion_summary=completion_summary,
            deliverables=deliverables,
            tests_passed=tests_passed,
            documentation_updated=documentation_updated,
        )

    # Helper methods

    def _extract_components(self, content: str) -> List[str]:
        """Extract component names from design"""
        import re
        # Look for component patterns
        pattern = r'([A-Z][a-zA-Z]+Component|[A-Z][a-zA-Z]+\.tsx)'
        matches = re.findall(pattern, content)
        return list(set(matches))[:20]

    def _extract_reusable(self, content: str) -> List[str]:
        """Extract reusable components"""
        components = []
        lines = content.split('\n')
        in_reusable_section = False
        for line in lines:
            if 'reusable' in line.lower() and ':' in line:
                in_reusable_section = True
                continue
            if in_reusable_section and line.strip().startswith('-'):
                components.append(line.strip()[1:].strip())
            elif in_reusable_section and not line.strip().startswith('-'):
                in_reusable_section = False
        return components[:10]
