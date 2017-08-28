/*!
 * \file  SysMgrCmp.h
 * \brief Interfaces of Component manager only
 * 
 * It might be needed for plaformization purpose to include this SysMgrCmp.h instead of SysManager.h
 * for FW platform components that are generic and thus do not know application adaptation (such as system states, ...),
 * but need to be included in the component manager
 * 
 */

#ifndef SYSMGRCMP_H
#define SYSMGRCMP_H


/*! 
 * \def DEFAULT_TASK_CREATION_PRIORITY
 * \brief May be used when creating a system task (ie that is defined in SYSADAPT_SystemTasks)
 * 
 * Priority will be overwritten by System Manager with information in SYSADAPT_SystemTasks[]
 *
 */
#define DEFAULT_TASK_CREATION_PRIORITY		255


/*! 
 * \enum E_CMP_HOOKS
 * \brief Define the successive initialization hooks of components of the system
 *
 * Hooks CMP_XXX_FIRST and CMP_XXX_END are defined to be able to insert initializations steps if needed
 */
typedef enum
{
    CMP_INITHW_FIRST = 0,
    CMP_INITHW,
    CMP_INITHW_END,
    CMP_INITVAR_FIRST,
    CMP_INITVAR,
    CMP_INITVAR_END,
    CMP_INITTASKS_FIRST,
    CMP_INITTASKS,
    CMP_INITTASKS_END,
    CMP_LASTINIT_FIRST,
    CMP_LASTINIT,
    CMP_LASTINIT_END,
    CMP_CYCLE
} E_CMP_HOOKS;



/*! 
 * \enum E_RES_HOOK_CALL
 * \brief Define the return code for hook functions
 *
 */
typedef enum
{
    HOOK_CALL_OK = 0,
    HOOK_CALL_FATALERROR
} E_RES_HOOK_CALL;



#endif  // SYSMGRCMP_H
