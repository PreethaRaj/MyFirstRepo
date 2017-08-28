/*!
 * \file  CmpExample.h
 * \brief Interfaces of CmpExample component
 *
 * [CODING_RULE] : must contains all interfaces of the component with the outside 
 *
 * [CODING_RULE] : must contains only interfaces of the component with the outside
 *
 * [CODING_RULE] : this header file must be autosufficient (a component that need to use a function or type of this component has to include only this file)
 *
 * [CODING_RULE] : it is not allowed to export global variables outside of a component. Use function to access such variables.
 * Global variables for internal use inside a component are allowed but thus they can not be declared in this .h
 *
 */

#ifndef CMPEXAMPLE_H
#define CMPEXAMPLE_H
   
//Preetha
#include "../SysManager/SysManager.h"

E_RES_HOOK_CALL CmpExample(E_CMP_HOOKS hook);

void EXAMPLE_FunctionToBeExportedToOutside(void);

#endif // CMPEXAMPLE_H
