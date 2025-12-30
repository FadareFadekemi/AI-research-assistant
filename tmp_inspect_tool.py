import inspect
import crewai.tools as t
print('module file:', t.__file__)
print('tool object:', t.tool)
print('\n---source---\n')
print(inspect.getsource(t.tool))
